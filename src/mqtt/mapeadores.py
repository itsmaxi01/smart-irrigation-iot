import json
from collections.abc import Mapping
from enum import Enum

from dominio.enumeraciones import (
    EstadoValvula,
    Lluvia,
    Modo,
    Radiacion,
    VelocidadRiego,
)
from mqtt.topics import (
    TOPIC_DISPONIBILIDAD,
    TOPIC_ESTADO,
    TOPIC_MODO,
    TOPIC_VALVULA,
    TOPIC_VELOCIDAD,
    TOPICS_DISCOVERY,
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

_DISPOSITIVO_HOME_ASSISTANT = {
    "identifiers": ["cuby-irrigation"],
    "name": "Cuby Irrigation",
    "manufacturer": "Smart Irrigation IoT Simulator",
    "model": "Simulator",
}


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


def mensajes_discovery() -> tuple[tuple[str, str], ...]:
    comunes = {
        "state_topic": TOPIC_ESTADO,
        "availability_topic": TOPIC_DISPONIBILIDAD,
        "payload_available": "online",
        "payload_not_available": "offline",
        "device": _DISPOSITIVO_HOME_ASSISTANT,
    }
    configuraciones = (
        {
            **comunes,
            "name": "Mode",
            "unique_id": "cuby_irrigation_mode",
            "command_topic": TOPIC_MODO,
            "value_template": "{{ value_json.mode }}",
            "options": ["AUTOMATICO", "MANUAL"],
        },
        {
            **comunes,
            "name": "Irrigation speed",
            "unique_id": "cuby_irrigation_speed",
            "command_topic": TOPIC_VELOCIDAD,
            "value_template": "{{ value_json.irrigation_speed }}",
            "options": ["BAJA", "MEDIA", "ALTA"],
        },
        {
            **comunes,
            "name": "Valve",
            "unique_id": "cuby_irrigation_valve",
            "command_topic": TOPIC_VALVULA,
            "value_template": "{{ value_json.valve }}",
            "payload_on": "ABIERTA",
            "payload_off": "CERRADA",
            "state_on": "ABIERTA",
            "state_off": "CERRADA",
        },
        _configuracion_sensor(comunes, "Soil moisture", "soil_moisture", "%", "moisture"),
        _configuracion_sensor(comunes, "Water level", "water_level", "%"),
        _configuracion_sensor(comunes, "Minimum moisture", "minimum_moisture", "%"),
        _configuracion_sensor(comunes, "Target moisture", "target_moisture", "%"),
        _configuracion_sensor(comunes, "Temperature", "temperature", "°C", "temperature"),
        _configuracion_sensor(comunes, "Ambient humidity", "ambient_humidity", "%", "humidity"),
        _configuracion_sensor(comunes, "Radiation", "radiation"),
        _configuracion_sensor(comunes, "Rain", "rain"),
    )
    return tuple(
        (topic, json.dumps(configuracion, separators=(",", ":")))
        for topic, configuracion in zip(TOPICS_DISCOVERY, configuraciones, strict=True)
    )


def _configuracion_sensor(
    comunes: Mapping[str, object],
    nombre: str,
    clave: str,
    unidad: str | None = None,
    clase_dispositivo: str | None = None,
) -> dict[str, object]:
    configuracion: dict[str, object] = {
        **comunes,
        "name": nombre,
        "unique_id": f"cuby_irrigation_{clave}",
        "value_template": f"{{{{ value_json.{clave} }}}}",
    }
    if unidad is not None:
        configuracion["unit_of_measurement"] = unidad
    if clase_dispositivo is not None:
        configuracion["device_class"] = clase_dispositivo
    return configuracion


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
