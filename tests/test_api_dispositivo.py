import pytest
from fastapi.testclient import TestClient

from api.principal import app, dispositivo, servicio_dispositivo
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
def test_cambia_velocidad_en_cualquier_modo(modo: Modo) -> None:
    servicio_dispositivo.cambiar_modo(modo)

    respuesta = cliente.patch("/api/device/speed", json={"speed": "ALTA"})

    assert respuesta.status_code == 200
    assert respuesta.json()["irrigation_speed"] == "ALTA"


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
        ("/api/device/mode", {"mode": "SUPERSAIYAJIN"}),
        ("/api/device/speed", {"speed": "TURBO"}),
        ("/api/device/valve", {"state": "ENTREABIERTA"}),
    ],
)
def test_rechaza_valores_invalidos(ruta: str, payload: dict[str, str]) -> None:
    respuesta = cliente.patch(ruta, json=payload)

    assert respuesta.status_code == 422


def test_cambio_es_visible_en_obtencion_posterior() -> None:
    cliente.patch("/api/device/mode", json={"mode": "AUTOMATICO"})

    respuesta = cliente.get("/api/device")

    assert respuesta.json()["mode"] == "AUTOMATICO"


def test_api_y_servicio_comparten_la_misma_instancia() -> None:
    cliente.patch("/api/device/speed", json={"speed": "ALTA"})

    assert servicio_dispositivo.dispositivo is dispositivo
    assert dispositivo.velocidad_riego == VelocidadRiego.ALTA


def test_cambiar_velocidad_no_modifica_humedad_ni_agua() -> None:
    humedad_inicial = dispositivo.humedad_suelo
    agua_inicial = dispositivo.nivel_agua

    respuesta = cliente.patch("/api/device/speed", json={"speed": "ALTA"})

    assert respuesta.status_code == 200
    assert respuesta.json()["soil_moisture"] == humedad_inicial
    assert respuesta.json()["water_level"] == agua_inicial
