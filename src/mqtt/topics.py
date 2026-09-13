TOPIC_ESTADO = "smart-irrigation/device/state"
TOPIC_MODO = "smart-irrigation/device/mode/set"
TOPIC_VELOCIDAD = "smart-irrigation/device/speed/set"
TOPIC_VALVULA = "smart-irrigation/device/valve/set"
TOPIC_DISPONIBILIDAD = "cuby/irrigation/availability"
TOPIC_ESTADO_HOME_ASSISTANT = "homeassistant/status"

TOPICS_COMANDOS = (TOPIC_MODO, TOPIC_VELOCIDAD, TOPIC_VALVULA)

TOPICS_DISCOVERY = (
    "homeassistant/select/cuby_irrigation/mode/config",
    "homeassistant/select/cuby_irrigation/speed/config",
    "homeassistant/switch/cuby_irrigation/valve/config",
    "homeassistant/sensor/cuby_irrigation/soil_moisture/config",
    "homeassistant/sensor/cuby_irrigation/water_level/config",
    "homeassistant/sensor/cuby_irrigation/minimum_moisture/config",
    "homeassistant/sensor/cuby_irrigation/target_moisture/config",
    "homeassistant/sensor/cuby_irrigation/temperature/config",
    "homeassistant/sensor/cuby_irrigation/ambient_humidity/config",
    "homeassistant/sensor/cuby_irrigation/radiation/config",
    "homeassistant/sensor/cuby_irrigation/rain/config",
)
