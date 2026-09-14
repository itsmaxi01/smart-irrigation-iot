import json

import pytest

from dominio.enumeraciones import (
    EstadoValvula,
    Lluvia,
    Modo,
    Radiacion,
    VelocidadRiego,
)
from mqtt.mapeadores import (
    mensajes_discovery,
    payload_a_estado_valvula,
    payload_a_modo,
    payload_a_velocidad,
    snapshot_a_payload,
)


def test_discovery_define_precision_de_sensores_numericos() -> None:
    configuraciones = {
        json.loads(payload)["unique_id"]: json.loads(payload)
        for _, payload in mensajes_discovery()
    }

    assert configuraciones["cuby_irrigation_soil_moisture"][
        "suggested_display_precision"
    ] == 1
    assert configuraciones["cuby_irrigation_water_level"][
        "suggested_display_precision"
    ] == 1
    assert configuraciones["cuby_irrigation_minimum_moisture"][
        "suggested_display_precision"
    ] == 0
    assert configuraciones["cuby_irrigation_target_moisture"][
        "suggested_display_precision"
    ] == 0


def test_discovery_usa_nombre_visible_del_proyecto_sin_cambiar_identificador() -> None:
    _, payload = mensajes_discovery()[0]
    dispositivo = json.loads(payload)["device"]

    assert dispositivo["name"] == "Smart Irrigation"
    assert dispositivo["identifiers"] == ["cuby-irrigation"]


def test_discovery_define_entity_ids_estables_para_dashboard() -> None:
    configuraciones = {
        json.loads(payload)["unique_id"]: json.loads(payload)
        for _, payload in mensajes_discovery()
    }

    assert configuraciones["cuby_irrigation_mode"]["default_entity_id"] == (
        "select.cuby_irrigation_mode"
    )
    assert configuraciones["cuby_irrigation_speed"]["default_entity_id"] == (
        "select.cuby_irrigation_irrigation_speed"
    )
    assert configuraciones["cuby_irrigation_valve"]["default_entity_id"] == (
        "switch.cuby_irrigation_valve"
    )
    assert configuraciones["cuby_irrigation_soil_moisture"]["default_entity_id"] == (
        "sensor.cuby_irrigation_soil_moisture"
    )


def test_mapea_snapshot_completo_a_payload_json() -> None:
    estado = (
        Modo.AUTOMATICO,
        EstadoValvula.CERRADA,
        VelocidadRiego.MEDIA,
        42.7,
        76.4,
        30.0,
        60.0,
    )
    condiciones = (25.0, 50.0, Radiacion.MEDIA, Lluvia.NINGUNA)

    payload = snapshot_a_payload(estado, condiciones)

    assert json.loads(payload) == {
        "mode": "AUTOMATICO",
        "valve": "CERRADA",
        "irrigation_speed": "MEDIA",
        "soil_moisture": 42.7,
        "water_level": 76.4,
        "minimum_moisture": 30.0,
        "target_moisture": 60.0,
        "temperature": 25.0,
        "ambient_humidity": 50.0,
        "radiation": "MEDIA",
        "rain": "NINGUNA",
    }


@pytest.mark.parametrize(
    ("mapeador", "payload", "esperado"),
    [
        (payload_a_modo, "AUTOMATICO", Modo.AUTOMATICO),
        (payload_a_modo, "MANUAL", Modo.MANUAL),
        (payload_a_velocidad, "BAJA", VelocidadRiego.BAJA),
        (payload_a_velocidad, "MEDIA", VelocidadRiego.MEDIA),
        (payload_a_velocidad, "ALTA", VelocidadRiego.ALTA),
        (payload_a_estado_valvula, "ABIERTA", EstadoValvula.ABIERTA),
        (payload_a_estado_valvula, "CERRADA", EstadoValvula.CERRADA),
    ],
)
def test_mapea_payload_valido_a_enum(mapeador, payload: str, esperado: object) -> None:
    assert mapeador(payload) == esperado


@pytest.mark.parametrize(
    ("mapeador", "payload"),
    [
        (payload_a_modo, "automatico"),
        (payload_a_velocidad, "RAPIDA"),
        (payload_a_estado_valvula, "OPEN"),
    ],
)
def test_rechaza_payload_de_comando_invalido(mapeador, payload: str) -> None:
    with pytest.raises(ValueError, match="no válido"):
        mapeador(payload)
