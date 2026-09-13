import json
from collections.abc import Callable
from threading import Lock
from unittest.mock import MagicMock, call

import pytest
from paho.mqtt.enums import CallbackAPIVersion

import mqtt.cliente as modulo_cliente
from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import (
    EstadoValvula,
    Lluvia,
    Modo,
    Radiacion,
    VelocidadRiego,
)
from mqtt.cliente import QOS, ClienteMqtt
from mqtt.mapeadores import CondicionesAmbiente
from mqtt.topics import (
    TOPIC_DISPONIBILIDAD,
    TOPIC_ESTADO,
    TOPIC_ESTADO_HOME_ASSISTANT,
    TOPIC_MODO,
    TOPIC_VALVULA,
    TOPIC_VELOCIDAD,
    TOPICS_COMANDOS,
    TOPICS_DISCOVERY,
)

CONDICIONES: CondicionesAmbiente = (
    25.0,
    50.0,
    Radiacion.MEDIA,
    Lluvia.NINGUNA,
)


def crear_dispositivo(modo: Modo = Modo.MANUAL) -> DispositivoRiego:
    return DispositivoRiego(
        modo=modo,
        velocidad_riego=VelocidadRiego.MEDIA,
        humedad_suelo=40,
        nivel_agua=80,
        humedad_minima=30,
        humedad_objetivo=60,
    )


def crear_cliente(
    monkeypatch: pytest.MonkeyPatch,
    servicio: ServicioDispositivo,
) -> tuple[ClienteMqtt, MagicMock]:
    cliente_paho = MagicMock()
    monkeypatch.setattr(modulo_cliente.paho, "Client", lambda **_: cliente_paho)
    return ClienteMqtt(servicio, lambda: CONDICIONES), cliente_paho


def marcar_conectado(cliente: ClienteMqtt) -> None:
    cliente._conectado = True


@pytest.mark.parametrize(
    ("topic", "payload", "obtener_valor", "esperado"),
    [
        (TOPIC_MODO, b"AUTOMATICO", lambda d: d.modo, Modo.AUTOMATICO),
        (
            TOPIC_VELOCIDAD,
            b"ALTA",
            lambda d: d.velocidad_riego,
            VelocidadRiego.ALTA,
        ),
        (
            TOPIC_VALVULA,
            b"ABIERTA",
            lambda d: d.estado_valvula,
            EstadoValvula.ABIERTA,
        ),
    ],
)
def test_comando_mqtt_usa_servicio_dispositivo(
    monkeypatch: pytest.MonkeyPatch,
    topic: str,
    payload: bytes,
    obtener_valor: Callable[[DispositivoRiego], object],
    esperado: object,
) -> None:
    dispositivo = crear_dispositivo()
    servicio = ServicioDispositivo(dispositivo, Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)
    marcar_conectado(cliente)

    cliente.procesar_mensaje(topic, payload)

    assert obtener_valor(dispositivo) == esperado
    cliente_paho.publish.assert_called_once()
    assert cliente_paho.publish.call_args.args[0] == TOPIC_ESTADO


@pytest.mark.parametrize(
    ("topic", "payload"),
    [
        (TOPIC_MODO, b"automatico"),
        (TOPIC_VELOCIDAD, b"RAPIDA"),
        (TOPIC_VALVULA, b"OPEN"),
        ("smart-irrigation/device/desconocido/set", b"MANUAL"),
        (TOPIC_MODO, b"\xff"),
    ],
)
def test_payload_invalido_no_rompe_cliente_ni_publica_estado(
    monkeypatch: pytest.MonkeyPatch,
    topic: str,
    payload: bytes,
) -> None:
    dispositivo = crear_dispositivo()
    servicio = ServicioDispositivo(dispositivo, Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)

    cliente.procesar_mensaje(topic, payload)

    assert dispositivo.modo == Modo.MANUAL
    assert dispositivo.velocidad_riego == VelocidadRiego.MEDIA
    assert dispositivo.estado_valvula == EstadoValvula.CERRADA
    cliente_paho.publish.assert_not_called()


def test_politica_de_valvula_en_automatico_es_la_misma_que_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo(Modo.AUTOMATICO)
    servicio = ServicioDispositivo(dispositivo, Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)

    cliente.procesar_mensaje(TOPIC_VALVULA, b"ABIERTA")

    assert dispositivo.estado_valvula == EstadoValvula.CERRADA
    cliente_paho.publish.assert_not_called()


def test_iniciar_y_detener_delega_en_paho(monkeypatch: pytest.MonkeyPatch) -> None:
    servicio = ServicioDispositivo(crear_dispositivo(), Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)

    cliente.iniciar()
    cliente.detener()

    cliente_paho.connect_async.assert_called_once_with("localhost", 1883)
    cliente_paho.loop_start.assert_called_once_with()
    cliente_paho.disconnect.assert_called_once_with()
    cliente_paho.loop_stop.assert_called_once_with()


def test_configura_callback_api_version2_backoff_y_lwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cliente_paho = MagicMock()
    fabrica_paho = MagicMock(return_value=cliente_paho)
    monkeypatch.setattr(modulo_cliente.paho, "Client", fabrica_paho)
    servicio = ServicioDispositivo(crear_dispositivo(), Lock())
    ClienteMqtt(servicio, lambda: CONDICIONES)

    fabrica_paho.assert_called_once_with(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="smart-irrigation-simulator",
    )
    cliente_paho.reconnect_delay_set.assert_called_once_with(min_delay=1, max_delay=30)
    cliente_paho.will_set.assert_called_once_with(
        TOPIC_DISPONIBILIDAD,
        payload="offline",
        qos=QOS,
        retain=True,
    )


def test_al_conectar_suscribe_y_resincroniza_estado_actual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    servicio = ServicioDispositivo(dispositivo, Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)
    codigo_conexion = MagicMock(is_failure=False)

    cliente._al_conectar(
        cliente_paho,
        object(),
        MagicMock(),
        codigo_conexion,
        None,
    )

    cliente_paho.subscribe.assert_called_once_with(
        [
            *((topic, QOS) for topic in TOPICS_COMANDOS),
            (TOPIC_ESTADO_HOME_ASSISTANT, QOS),
        ]
    )
    publicaciones = cliente_paho.publish.call_args_list
    assert call(TOPIC_DISPONIBILIDAD, "online", qos=QOS, retain=True) in publicaciones
    for topic in TOPICS_DISCOVERY:
        assert any(
            llamada.args[0] == topic
            and llamada.kwargs == {"qos": QOS, "retain": True}
            for llamada in publicaciones
        )

    estado_publicado = next(llamada for llamada in publicaciones if llamada.args[0] == TOPIC_ESTADO)
    assert json.loads(estado_publicado.args[1])["mode"] == "MANUAL"
    assert estado_publicado.kwargs == {"qos": QOS, "retain": True}


def test_home_assistant_online_republica_discovery_y_estado_actual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    servicio = ServicioDispositivo(dispositivo, Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)
    marcar_conectado(cliente)
    dispositivo.cambiar_velocidad_riego(VelocidadRiego.ALTA)

    cliente.procesar_mensaje(TOPIC_ESTADO_HOME_ASSISTANT, b"online")

    publicaciones = cliente_paho.publish.call_args_list
    assert {llamada.args[0] for llamada in publicaciones[:-1]} == set(TOPICS_DISCOVERY)
    assert publicaciones[-1].args[0] == TOPIC_ESTADO
    assert json.loads(publicaciones[-1].args[1])["irrigation_speed"] == "ALTA"
    assert all(
        llamada.kwargs == {"qos": QOS, "retain": True} for llamada in publicaciones
    )


def test_fallo_de_publicacion_mqtt_no_se_propaga_al_simulador(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    servicio = ServicioDispositivo(crear_dispositivo(), Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)
    marcar_conectado(cliente)
    cliente_paho.publish.side_effect = OSError("broker desconectado")

    cliente.publicar_estado()

    cliente_paho.publish.assert_called_once_with(
        TOPIC_ESTADO,
        cliente_paho.publish.call_args.args[1],
        qos=QOS,
        retain=True,
    )


def test_estado_no_se_encola_mientras_mqtt_esta_desconectado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    servicio = ServicioDispositivo(crear_dispositivo(), Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)

    cliente.publicar_estado()

    cliente_paho.publish.assert_not_called()


def test_shutdown_limpio_publica_offline_si_estaba_conectado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    servicio = ServicioDispositivo(crear_dispositivo(), Lock())
    cliente, cliente_paho = crear_cliente(monkeypatch, servicio)
    cliente.iniciar()
    cliente._al_conectar(cliente_paho, object(), MagicMock(), MagicMock(is_failure=False), None)
    cliente_paho.publish.reset_mock()

    cliente.detener()

    cliente_paho.publish.assert_called_once_with(
        TOPIC_DISPONIBILIDAD,
        "offline",
        qos=QOS,
        retain=True,
    )
    cliente_paho.publish.return_value.wait_for_publish.assert_called_once_with(timeout=1.0)
    cliente_paho.disconnect.assert_called_once_with()
    cliente_paho.loop_stop.assert_called_once_with()
