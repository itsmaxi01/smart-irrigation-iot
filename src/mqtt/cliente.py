import logging
from collections.abc import Callable

import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.enumeraciones import EstadoValvula
from mqtt.configuracion import ConfiguracionMqtt
from mqtt.mapeadores import (
    CondicionesAmbiente,
    payload_a_estado_valvula,
    payload_a_modo,
    payload_a_velocidad,
    snapshot_a_payload,
)
from mqtt.topics import (
    TOPIC_ESTADO,
    TOPIC_MODO,
    TOPIC_VALVULA,
    TOPIC_VELOCIDAD,
    TOPICS_COMANDOS,
)

logger = logging.getLogger(__name__)


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
        self._cliente.on_message = self._al_recibir_mensaje

    def iniciar(self) -> None:
        self._cliente.connect(
            self._configuracion.host,
            self._configuracion.puerto,
        )
        self._cliente.loop_start()

    def detener(self) -> None:
        self._cliente.disconnect()
        self._cliente.loop_stop()

    def publicar_estado(
        self,
        condiciones: CondicionesAmbiente | None = None,
    ) -> None:
        estado = self._servicio_dispositivo.obtener_estado()
        condiciones_actuales = condiciones or self._obtener_condiciones()
        payload = snapshot_a_payload(estado, condiciones_actuales)
        self._cliente.publish(TOPIC_ESTADO, payload)

    def procesar_mensaje(self, topic: str, payload: bytes) -> None:
        try:
            comando = payload.decode("utf-8")
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

        cliente.subscribe([(topic, 0) for topic in TOPICS_COMANDOS])
        self.publicar_estado()

    def _al_recibir_mensaje(
        self,
        _cliente: paho.Client,
        _datos_usuario: object,
        mensaje: paho.MQTTMessage,
    ) -> None:
        self.procesar_mensaje(mensaje.topic, bytes(mensaje.payload))
