import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.errores import registrar_manejadores_errores, respuestas_error
from api.principal import app

cliente = TestClient(app)


def test_recurso_inexistente_usa_contrato_estandar() -> None:
    respuesta = cliente.get("/api/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "El recurso solicitado no existe",
        "fields": None,
    }


def test_metodo_no_permitido_usa_contrato_estandar() -> None:
    respuesta = cliente.post("/api/device")

    assert respuesta.status_code == 405
    assert respuesta.json() == {
        "code": "METHOD_NOT_ALLOWED",
        "message": "El método HTTP no está permitido para este recurso",
        "fields": None,
    }


def test_validacion_usa_campos_simples_y_codigo_estable() -> None:
    respuesta = cliente.put(
        "/api/environment/manual",
        json={
            "temperature": 25,
            "ambient_humidity": 101,
            "radiation": "MEDIA",
            "rain": "NINGUNA",
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json() == {
        "code": "VALIDATION_ERROR",
        "message": "Los datos enviados no son válidos",
        "fields": [
            {
                "field": "ambient_humidity",
                "message": "Debe ser menor o igual a 100",
            }
        ],
    }


def test_error_inesperado_se_registra_y_no_filtra_detalles(
    caplog,
) -> None:
    app_prueba = FastAPI()
    registrar_manejadores_errores(app_prueba)

    @app_prueba.get("/fallo", responses=respuestas_error(500))
    def producir_error() -> None:
        raise RuntimeError("detalle interno secreto")

    cliente_prueba = TestClient(app_prueba, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="api.errores"):
        respuesta = cliente_prueba.get("/fallo")

    assert respuesta.status_code == 500
    assert respuesta.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Ocurrió un error interno",
        "fields": None,
    }
    assert "Error inesperado procesando GET /fallo" in caplog.text
    assert "detalle interno secreto" in caplog.text
    assert "detalle interno secreto" not in respuesta.text


def test_openapi_documenta_el_contrato_de_error() -> None:
    esquema = app.openapi()
    respuestas_valvula = esquema["paths"]["/api/device/valve"]["patch"]["responses"]
    respuestas_ambiente = esquema["paths"]["/api/environment/manual"]["put"][
        "responses"
    ]

    for respuestas in (respuestas_valvula, respuestas_ambiente):
        for status_code in ("404", "405", "409", "422", "500"):
            referencia = respuestas[status_code]["content"]["application/json"]["schema"][
                "$ref"
            ]
            assert referencia == "#/components/schemas/RespuestaError"

    propiedad_codigo = esquema["components"]["schemas"]["RespuestaError"]["properties"][
        "code"
    ]
    assert propiedad_codigo["$ref"] == "#/components/schemas/CodigoError"
    codigo = esquema["components"]["schemas"]["CodigoError"]
    assert codigo["enum"] == [
        "VALIDATION_ERROR",
        "MANUAL_ENVIRONMENT_REQUIRED",
        "VALVE_CONTROL_REQUIRES_MANUAL_MODE",
        "RESOURCE_NOT_FOUND",
        "METHOD_NOT_ALLOWED",
        "INTERNAL_ERROR",
    ]
