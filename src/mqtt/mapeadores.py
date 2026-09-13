import json
from enum import Enum

from dominio.enumeraciones import (
    EstadoValvula,
    Lluvia,
    Modo,
    Radiacion,
    VelocidadRiego,
)

type EstadoDispositivo = tuple[
    Modo,
    EstadoValvula,
    VelocidadRiego,
    float,
    float,
    float,
    float,
]
type CondicionesAmbiente = tuple[float, float, Radiacion, Lluvia]


def snapshot_a_payload(
    estado: EstadoDispositivo,
    condiciones: CondicionesAmbiente,
) -> str:
    (
        modo,
        estado_valvula,
        velocidad_riego,
        humedad_suelo,
        nivel_agua,
        humedad_minima,
        humedad_objetivo,
    ) = estado
    temperatura, humedad_ambiente, radiacion, lluvia = condiciones

    return json.dumps(
        {
            "mode": modo.name,
            "valve": estado_valvula.name,
            "irrigation_speed": velocidad_riego.name,
            "soil_moisture": humedad_suelo,
            "water_level": nivel_agua,
            "minimum_moisture": humedad_minima,
            "target_moisture": humedad_objetivo,
            "temperature": temperatura,
            "ambient_humidity": humedad_ambiente,
            "radiation": radiacion.name,
            "rain": lluvia.name,
        },
        separators=(",", ":"),
    )


def payload_a_modo(payload: str) -> Modo:
    return _payload_a_enum(payload, Modo, "modo")


def payload_a_velocidad(payload: str) -> VelocidadRiego:
    return _payload_a_enum(payload, VelocidadRiego, "velocidad")


def payload_a_estado_valvula(payload: str) -> EstadoValvula:
    return _payload_a_enum(payload, EstadoValvula, "estado de válvula")


def _payload_a_enum[T: Enum](payload: str, enum: type[T], descripcion: str) -> T:
    valor = payload.strip()
    try:
        return enum[valor]
    except KeyError as error:
        raise ValueError(f"Payload de {descripcion} no válido: {valor!r}") from error
