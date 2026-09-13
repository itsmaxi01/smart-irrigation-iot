from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfiguracionMqtt:
    host: str = "localhost"
    puerto: int = 1883
    client_id: str = "smart-irrigation-simulator"
