import logging
from collections.abc import Callable

import paho.mqtt.client as paho
from paho.mqtt import MQTTException
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.enumeraciones import EstadoValvula
from mqtt.configuracion import ConfiguracionMqtt
from mqtt.mapeadores import (
    CondicionesAmbiente,
    mensajes_discovery,
    payload_a_estado_valvula,
    payload_a_modo,
    payload_a_velocidad,
    snapshot_a_payload,
)
from mqtt.topics import (
    TOPIC_DISPONIBILIDAD,
    TOPIC_ESTADO,
    TOPIC_ESTADO_HOME_ASSISTANT,
    TOPIC_MODO,
    TOPIC_VALVULA,
    TOPIC_VELOCIDAD,
    TOPICS_COMANDOS,
)

logger = logging.getLogger(__name__)
QOS = 1


class ClienteMqtt:
    def __init__(
        self,
        servicio_dispositivo: ServicioDispositivo,
        obtener_condiciones: Callable[[], CondicionesAmbiente],
        configuracion: ConfiguracionMqtt | None = None,
    ) -> None:
        self._servicio_dispositivo = servicio_dispositivo
        self._obtener_condiciones = obtener_condiciones
        self._configuracion = configuracion or ConfiguracionMqtt()
        self._cliente = paho.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=self._configuracion.client_id,
        )
        self._cliente.on_connect = self._al_conectar
        self._cliente.on_connect_fail = self._al_fallar_conexion
        self._cliente.on_disconnect = self._al_desconectar
        self._cliente.on_message = self._al_recibir_mensaje
        self._cliente.reconnect_delay_set(
            min_delay=self._configuracion.demora_reconexion_minima,
            max_delay=self._configuracion.demora_reconexion_maxima,
        )
        self._cliente.will_set(
            TOPIC_DISPONIBILIDAD,
            payload="offline",
            qos=QOS,
            retain=True,
        )
        self._iniciado = False
        self._conectado = False
        self._conecto_alguna_vez = False

    def iniciar(self) -> None:
        if self._iniciado:
            return

        logger.info(
            "Iniciando MQTT en %s:%s",
            self._configuracion.host,
            self._configuracion.puerto,
        )
        self._iniciado = True
        self._cliente.connect_async(
            self._configuracion.host,
            self._configuracion.puerto,
        )
        self._cliente.loop_start()

    def detener(self) -> None:
        if not self._iniciado:
            return

        logger.info("Deteniendo cliente MQTT")
        self._iniciado = False
        if self._conectado:
            publicacion = self._publicar(TOPIC_DISPONIBILIDAD, "offline", retain=True)
            if publicacion is not None:
                try:
                    publicacion.wait_for_publish(timeout=1.0)
                except RuntimeError as error:
                    logger.warning("No se confirmó availability=offline: %s", error)
        self._cliente.disconnect()
        self._cliente.loop_stop()
        self._conectado = False

    def publicar_estado(
        self,
        condiciones: CondicionesAmbiente | None = None,
    ) -> None:
        estado = self._servicio_dispositivo.obtener_estado()
        condiciones_actuales = condiciones or self._obtener_condiciones()
        payload = snapshot_a_payload(estado, condiciones_actuales)
        self._publicar(TOPIC_ESTADO, payload, retain=True)

    def procesar_mensaje(self, topic: str, payload: bytes) -> None:
        try:
            comando = payload.decode("utf-8")
            if topic == TOPIC_ESTADO_HOME_ASSISTANT:
                self._procesar_estado_home_assistant(comando)
                return
            self._ejecutar_comando(topic, comando)
        except (UnicodeDecodeError, ValueError) as error:
            logger.warning("Comando MQTT rechazado en %s: %s", topic, error)
            return

        self.publicar_estado()

    def _ejecutar_comando(self, topic: str, payload: str) -> None:
        if topic == TOPIC_MODO:
            self._servicio_dispositivo.cambiar_modo(payload_a_modo(payload))
            return

        if topic == TOPIC_VELOCIDAD:
            self._servicio_dispositivo.cambiar_velocidad_riego(payload_a_velocidad(payload))
            return

        if topic == TOPIC_VALVULA:
            estado = payload_a_estado_valvula(payload)
            if estado == EstadoValvula.ABIERTA:
                self._servicio_dispositivo.abrir_valvula()
            else:
                self._servicio_dispositivo.cerrar_valvula()
            return

        raise ValueError(f"Topic de comando no reconocido: {topic}")

    def _al_conectar(
        self,
        cliente: paho.Client,
        _datos_usuario: object,
        _banderas: paho.ConnectFlags,
        codigo: ReasonCode,
        _propiedades: Properties | None,
    ) -> None:
        if codigo.is_failure:
            logger.warning("Conexión MQTT rechazada: %s", codigo)
            return

        recuperada = self._conecto_alguna_vez
        self._conectado = True
        self._conecto_alguna_vez = True
        if recuperada:
            logger.info("Conexión MQTT recuperada; resincronizando")
        else:
            logger.info("Conexión MQTT establecida; sincronizando")

        cliente.subscribe(
            [
                *((topic, QOS) for topic in TOPICS_COMANDOS),
                (TOPIC_ESTADO_HOME_ASSISTANT, QOS),
            ]
        )
        self._publicar(TOPIC_DISPONIBILIDAD, "online", retain=True)
        self.publicar_discovery()
        self.publicar_estado()

    def _al_fallar_conexion(
        self,
        _cliente: paho.Client,
        _datos_usuario: object,
    ) -> None:
        if not self._conecto_alguna_vez:
            logger.warning("Broker MQTT no disponible al iniciar; Paho reintentará en background")
        else:
            logger.warning("Falló un intento de reconexión MQTT; Paho continuará reintentando")

    def _al_desconectar(
        self,
        _cliente: paho.Client,
        _datos_usuario: object,
        _banderas: paho.DisconnectFlags,
        codigo: ReasonCode,
        _propiedades: Properties | None,
    ) -> None:
        self._conectado = False
        if self._iniciado:
            logger.warning("Conexión MQTT perdida (%s); esperando reconexión automática", codigo)

    def publicar_discovery(self) -> None:
        for topic, payload in mensajes_discovery():
            self._publicar(topic, payload, retain=True)

    def _procesar_estado_home_assistant(self, payload: str) -> None:
        if payload.strip() != "online":
            return

        logger.info("Home Assistant inició o reinició; resincronizando MQTT")
        self.publicar_discovery()
        self.publicar_estado()

    def _publicar(
        self,
        topic: str,
        payload: str,
        *,
        retain: bool,
    ) -> paho.MQTTMessageInfo | None:
        if not self._conectado:
            return None

        try:
            return self._cliente.publish(topic, payload, qos=QOS, retain=retain)
        except (OSError, MQTTException) as error:
            logger.warning("No se pudo publicar MQTT en %s: %s", topic, error)
            return None

    def _al_recibir_mensaje(
        self,
        _cliente: paho.Client,
        _datos_usuario: object,
        mensaje: paho.MQTTMessage,
    ) -> None:
        self.procesar_mensaje(mensaje.topic, bytes(mensaje.payload))
