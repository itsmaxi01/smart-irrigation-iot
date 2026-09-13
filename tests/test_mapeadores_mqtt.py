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
    payload_a_estado_valvula,
    payload_a_modo,
    payload_a_velocidad,
    snapshot_a_payload,
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
