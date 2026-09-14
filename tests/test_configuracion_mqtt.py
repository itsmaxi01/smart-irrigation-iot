import pytest

from mqtt.configuracion import ConfiguracionMqtt

VARIABLES_MQTT = ("MQTT_HOST", "MQTT_PORT", "MQTT_CLIENT_ID")


def test_configuracion_desde_entorno_usa_defaults_locales(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in VARIABLES_MQTT:
        monkeypatch.delenv(variable, raising=False)

    configuracion = ConfiguracionMqtt.desde_entorno()

    assert configuracion.host == "localhost"
    assert configuracion.puerto == 1883
    assert configuracion.client_id == "smart-irrigation-simulator"


def test_configuracion_desde_entorno_usa_broker_docker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MQTT_HOST", "mosquitto")
    monkeypatch.setenv("MQTT_PORT", "1883")
    monkeypatch.setenv("MQTT_CLIENT_ID", "simulator-compose")

    configuracion = ConfiguracionMqtt.desde_entorno()

    assert configuracion.host == "mosquitto"
    assert configuracion.puerto == 1883
    assert configuracion.client_id == "simulator-compose"


def test_configuracion_desde_entorno_rechaza_puerto_invalido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MQTT_PORT", "invalido")

    with pytest.raises(ValueError):
        ConfiguracionMqtt.desde_entorno()
