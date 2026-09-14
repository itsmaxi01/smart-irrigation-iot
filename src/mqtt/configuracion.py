import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfiguracionMqtt:
    host: str = "localhost"
    puerto: int = 1883
    client_id: str = "smart-irrigation-simulator"
    demora_reconexion_minima: int = 1
    demora_reconexion_maxima: int = 30

    @classmethod
    def desde_entorno(cls) -> "ConfiguracionMqtt":
        return cls(
            host=os.getenv("MQTT_HOST", "localhost"),
            puerto=int(os.getenv("MQTT_PORT", "1883")),
            client_id=os.getenv(
                "MQTT_CLIENT_ID",
                "smart-irrigation-simulator",
            ),
        )
