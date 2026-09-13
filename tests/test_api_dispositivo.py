import pytest
from fastapi.testclient import TestClient

from api.principal import (
    app,
    cliente_mqtt,
    dispositivo,
    ejecutor_simulacion,
    servicio_dispositivo,
)
from dominio.enumeraciones import Modo, VelocidadRiego

cliente = TestClient(app)


@pytest.fixture(autouse=True)
def restablecer_estado_dispositivo() -> None:
    servicio_dispositivo.cambiar_modo(Modo.MANUAL)
    servicio_dispositivo.cerrar_valvula()
    servicio_dispositivo.cambiar_velocidad_riego(VelocidadRiego.MEDIA)


def test_obtener_dispositivo_devuelve_estado_completo() -> None:
    respuesta = cliente.get("/api/device")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "mode": "MANUAL",
        "valve": "CERRADA",
        "irrigation_speed": "MEDIA",
        "soil_moisture": 42.7,
        "water_level": 76.4,
        "minimum_moisture": 30.0,
        "target_moisture": 60.0,
    }


def test_cambia_modo_de_manual_a_automatico() -> None:
    respuesta = cliente.patch("/api/device/mode", json={"mode": "AUTOMATICO"})

    assert respuesta.status_code == 200
    assert respuesta.json()["mode"] == "AUTOMATICO"


def test_cambia_modo_de_automatico_a_manual() -> None:
    servicio_dispositivo.cambiar_modo(Modo.AUTOMATICO)

    respuesta = cliente.patch("/api/device/mode", json={"mode": "MANUAL"})

    assert respuesta.status_code == 200
    assert respuesta.json()["mode"] == "MANUAL"


@pytest.mark.parametrize("modo", [Modo.MANUAL, Modo.AUTOMATICO])
@pytest.mark.parametrize("velocidad", ["BAJA", "MEDIA", "ALTA"])
def test_acepta_velocidades_publicas_en_cualquier_modo(
    modo: Modo, velocidad: str
) -> None:
    servicio_dispositivo.cambiar_modo(modo)

    respuesta = cliente.patch("/api/device/speed", json={"speed": velocidad})

    assert respuesta.status_code == 200
    assert respuesta.json()["irrigation_speed"] == velocidad


def test_abre_valvula_en_manual() -> None:
    respuesta = cliente.patch("/api/device/valve", json={"state": "ABIERTA"})

    assert respuesta.status_code == 200
    assert respuesta.json()["valve"] == "ABIERTA"


def test_cierra_valvula_en_manual() -> None:
    servicio_dispositivo.abrir_valvula()

    respuesta = cliente.patch("/api/device/valve", json={"state": "CERRADA"})

    assert respuesta.status_code == 200
    assert respuesta.json()["valve"] == "CERRADA"


@pytest.mark.parametrize("estado", ["ABIERTA", "CERRADA"])
def test_rechaza_controlar_valvula_en_automatico(estado: str) -> None:
    servicio_dispositivo.cambiar_modo(Modo.AUTOMATICO)

    respuesta = cliente.patch("/api/device/valve", json={"state": estado})

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "detail": "La válvula solo puede controlarse en modo manual"
    }


@pytest.mark.parametrize(
    ("ruta", "payload"),
    [
        ("/api/device/mode", {"mode": "PEPINO"}),
        ("/api/device/speed", {"speed": "PEPINO"}),
        ("/api/device/valve", {"state": "PEPINO"}),
    ],
)
def test_rechaza_valores_invalidos(ruta: str, payload: dict[str, str]) -> None:
    respuesta = cliente.patch(ruta, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    ("ruta", "payload"),
    [
        ("/api/device/mode", {"mode": "automatico"}),
        ("/api/device/mode", {"mode": "manual"}),
        ("/api/device/speed", {"speed": 1}),
        ("/api/device/speed", {"speed": 2}),
        ("/api/device/speed", {"speed": 3}),
        ("/api/device/valve", {"state": "abierta"}),
        ("/api/device/valve", {"state": "cerrada"}),
    ],
)
def test_rechaza_valores_internos_del_dominio(
    ruta: str, payload: dict[str, str | int]
) -> None:
    respuesta = cliente.patch(ruta, json=payload)

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    ("ruta", "payload"),
    [
        ("/api/device/mode", {"mode": "MANUAL", "extra": True}),
        ("/api/device/speed", {"speed": "MEDIA", "extra": True}),
        ("/api/device/valve", {"state": "CERRADA", "extra": True}),
    ],
)
def test_rechaza_campos_extra(ruta: str, payload: dict[str, str | bool]) -> None:
    respuesta = cliente.patch(ruta, json=payload)

    assert respuesta.status_code == 422


def test_openapi_documenta_los_valores_publicos() -> None:
    esquemas = app.openapi()["components"]["schemas"]

    assert esquemas["CambiarModoRequest"]["properties"]["mode"]["enum"] == [
        "AUTOMATICO",
        "MANUAL",
    ]
    assert esquemas["CambiarVelocidadRequest"]["properties"]["speed"]["enum"] == [
        "BAJA",
        "MEDIA",
        "ALTA",
    ]
    assert esquemas["CambiarValvulaRequest"]["properties"]["state"]["enum"] == [
        "ABIERTA",
        "CERRADA",
    ]
    respuesta = esquemas["EstadoDispositivoResponse"]["properties"]
    assert respuesta["mode"]["enum"] == ["AUTOMATICO", "MANUAL"]
    assert respuesta["valve"]["enum"] == ["ABIERTA", "CERRADA"]
    assert respuesta["irrigation_speed"]["enum"] == ["BAJA", "MEDIA", "ALTA"]


def test_cambio_es_visible_en_obtencion_posterior() -> None:
    cliente.patch("/api/device/mode", json={"mode": "AUTOMATICO"})

    respuesta = cliente.get("/api/device")

    assert respuesta.json()["mode"] == "AUTOMATICO"


def test_api_modifica_la_instancia_compuesta_en_principal() -> None:
    cliente.patch("/api/device/speed", json={"speed": "ALTA"})

    estado = servicio_dispositivo.obtener_estado()
    assert estado[2] == VelocidadRiego.ALTA
    assert dispositivo.velocidad_riego == VelocidadRiego.ALTA


def test_lifespan_inicia_y_detiene_ejecutor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[str] = []

    monkeypatch.setattr(
        ejecutor_simulacion,
        "iniciar",
        lambda: llamadas.append("iniciar"),
    )
    monkeypatch.setattr(
        ejecutor_simulacion,
        "detener",
        lambda: llamadas.append("simulacion_detener"),
    )
    monkeypatch.setattr(
        cliente_mqtt,
        "iniciar",
        lambda: llamadas.append("mqtt_iniciar"),
    )
    monkeypatch.setattr(
        cliente_mqtt,
        "detener",
        lambda: llamadas.append("mqtt_detener"),
    )

    with TestClient(app):
        assert llamadas == ["mqtt_iniciar", "iniciar"]

    assert llamadas == [
        "mqtt_iniciar",
        "iniciar",
        "simulacion_detener",
        "mqtt_detener",
    ]


def test_cambiar_velocidad_no_modifica_humedad_ni_agua() -> None:
    humedad_inicial = dispositivo.humedad_suelo
    agua_inicial = dispositivo.nivel_agua

    respuesta = cliente.patch("/api/device/speed", json={"speed": "ALTA"})

    assert respuesta.status_code == 200
    assert respuesta.json()["soil_moisture"] == humedad_inicial
    assert respuesta.json()["water_level"] == agua_inicial
