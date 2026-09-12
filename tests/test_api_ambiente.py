import pytest
from fastapi.testclient import TestClient

from api.principal import (
    ambiente_aleatorio,
    ambiente_manual,
    app,
    ejecutor_simulacion,
    selector_ambiente,
)
from dominio.enumeraciones import FuenteAmbiente

cliente = TestClient(app)


@pytest.fixture(autouse=True)
def restablecer_fuente_ambiente() -> None:
    selector_ambiente.establecer_fuente_activa(FuenteAmbiente.ALEATORIO)


def test_obtener_fuente_devuelve_fuente_inicial_aleatoria() -> None:
    respuesta = cliente.get("/api/environment/source")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"source": "ALEATORIO"}


def test_obtener_ambiente_devuelve_condiciones_aleatorias_seleccionadas() -> None:
    temperatura, humedad, radiacion, lluvia = ambiente_aleatorio.obtener_condiciones()

    respuesta = cliente.get("/api/environment")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "source": "ALEATORIO",
        "temperature": temperatura,
        "ambient_humidity": humedad,
        "radiation": radiacion.name,
        "rain": lluvia.name,
    }


def test_obtener_ambiente_devuelve_condiciones_manuales_seleccionadas() -> None:
    selector_ambiente.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    temperatura, humedad, radiacion, lluvia = ambiente_manual.obtener_condiciones()

    respuesta = cliente.get("/api/environment")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "source": "MANUAL",
        "temperature": temperatura,
        "ambient_humidity": humedad,
        "radiation": radiacion.name,
        "rain": lluvia.name,
    }


def test_volver_a_aleatorio_recupera_las_condiciones_iniciales() -> None:
    condiciones_iniciales = ambiente_aleatorio.obtener_condiciones()
    cliente.patch("/api/environment/source", json={"source": "MANUAL"})
    cliente.patch("/api/environment/source", json={"source": "ALEATORIO"})

    respuesta = cliente.get("/api/environment")

    temperatura, humedad, radiacion, lluvia = condiciones_iniciales
    assert respuesta.json() == {
        "source": "ALEATORIO",
        "temperature": temperatura,
        "ambient_humidity": humedad,
        "radiation": radiacion.name,
        "rain": lluvia.name,
    }


def test_obtener_ambiente_no_modifica_condiciones() -> None:
    condiciones_aleatorias = ambiente_aleatorio.obtener_condiciones()
    condiciones_manuales = ambiente_manual.obtener_condiciones()

    cliente.get("/api/environment")
    selector_ambiente.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    cliente.get("/api/environment")

    assert ambiente_aleatorio.obtener_condiciones() == condiciones_aleatorias
    assert ambiente_manual.obtener_condiciones() == condiciones_manuales


def test_cambiar_fuente_a_manual_es_visible_en_obtencion_posterior() -> None:
    respuesta_cambio = cliente.patch(
        "/api/environment/source", json={"source": "MANUAL"}
    )
    respuesta_obtencion = cliente.get("/api/environment/source")

    assert respuesta_cambio.status_code == 200
    assert respuesta_cambio.json() == {"source": "MANUAL"}
    assert respuesta_obtencion.json() == {"source": "MANUAL"}


def test_cambiar_fuente_permite_volver_a_aleatorio() -> None:
    cliente.patch("/api/environment/source", json={"source": "MANUAL"})

    respuesta = cliente.patch(
        "/api/environment/source", json={"source": "ALEATORIO"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"source": "ALEATORIO"}


def test_rechaza_fuente_invalida() -> None:
    respuesta = cliente.patch(
        "/api/environment/source", json={"source": "CLIMA"}
    )

    assert respuesta.status_code == 422


def test_rechaza_campos_extra() -> None:
    respuesta = cliente.patch(
        "/api/environment/source",
        json={"source": "MANUAL", "extra": True},
    )

    assert respuesta.status_code == 422


def test_openapi_documenta_fuentes_publicas() -> None:
    esquemas = app.openapi()["components"]["schemas"]

    assert esquemas["CambiarFuenteAmbienteRequest"]["properties"]["source"]["enum"] == [
        "MANUAL",
        "ALEATORIO",
    ]
    assert esquemas["FuenteAmbienteResponse"]["properties"]["source"]["enum"] == [
        "MANUAL",
        "ALEATORIO",
    ]
    estado_ambiente = esquemas["EstadoAmbienteResponse"]["properties"]
    assert estado_ambiente["source"]["enum"] == ["MANUAL", "ALEATORIO"]
    assert estado_ambiente["radiation"]["enum"] == ["BAJA", "MEDIA", "ALTA"]
    assert estado_ambiente["rain"]["enum"] == [
        "NINGUNA",
        "LIGERA",
        "MODERADA",
        "FUERTE",
    ]


def test_api_y_ejecutor_comparten_selector_ambiente() -> None:
    cliente.patch("/api/environment/source", json={"source": "MANUAL"})

    assert selector_ambiente.fuente_activa == FuenteAmbiente.MANUAL
    assert ejecutor_simulacion._selector_ambiente is selector_ambiente
