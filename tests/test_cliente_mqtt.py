from collections.abc import Callable
from threading import Lock
from unittest.mock import MagicMock

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
from mqtt.cliente import ClienteMqtt
from mqtt.mapeadores import CondicionesAmbiente
from mqtt.topics import (
    TOPIC_ESTADO,
    TOPIC_MODO,
    TOPIC_VALVULA,
    TOPIC_VELOCIDAD,
    TOPICS_COMANDOS,
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

    cliente_paho.connect.assert_called_once_with("localhost", 1883)
    cliente_paho.loop_start.assert_called_once_with()
    cliente_paho.disconnect.assert_called_once_with()
    cliente_paho.loop_stop.assert_called_once_with()


def test_usa_callback_api_version2_y_se_suscribe_al_conectar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cliente_paho = MagicMock()
    fabrica_paho = MagicMock(return_value=cliente_paho)
    monkeypatch.setattr(modulo_cliente.paho, "Client", fabrica_paho)
    servicio = ServicioDispositivo(crear_dispositivo(), Lock())
    cliente = ClienteMqtt(servicio, lambda: CONDICIONES)
    codigo_conexion = MagicMock(is_failure=False)

    cliente._al_conectar(
        cliente_paho,
        object(),
        MagicMock(),
        codigo_conexion,
        None,
    )

    fabrica_paho.assert_called_once_with(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="smart-irrigation-simulator",
    )
    cliente_paho.subscribe.assert_called_once_with([(topic, 0) for topic in TOPICS_COMANDOS])
    cliente_paho.publish.assert_called_once()
