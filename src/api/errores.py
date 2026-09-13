import logging
from typing import Any, Literal, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

type CodigoError = Literal[
    "VALIDATION_ERROR",
    "MANUAL_ENVIRONMENT_REQUIRED",
    "VALVE_CONTROL_REQUIRES_MANUAL_MODE",
    "RESOURCE_NOT_FOUND",
    "METHOD_NOT_ALLOWED",
    "INTERNAL_ERROR",
]


class ErrorCampo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    message: str


class RespuestaError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: CodigoError
    message: str
    fields: list[ErrorCampo] | None = None


class ErrorApi(Exception):
    def __init__(self, status_code: int, code: CodigoError, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code: CodigoError = code
        self.message = message


_DESCRIPCIONES_HTTP = {
    404: "Recurso inexistente",
    405: "Método no permitido",
    409: "Conflicto con el estado actual",
    422: "Error de validación",
    500: "Error interno",
}


def respuestas_error(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": RespuestaError,
            "description": _DESCRIPCIONES_HTTP[status_code],
        }
        for status_code in status_codes
    }


def registrar_manejadores_errores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorApi, manejar_error_api)
    app.add_exception_handler(RequestValidationError, manejar_error_validacion)
    app.add_exception_handler(StarletteHTTPException, manejar_error_http)
    app.add_exception_handler(500, manejar_error_interno)


async def manejar_error_api(_request: Request, exception: Exception) -> JSONResponse:
    error = cast(ErrorApi, exception)
    return _respuesta_error(error.status_code, error.code, error.message)


async def manejar_error_validacion(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    error = cast(RequestValidationError, exception)
    fields = [_transformar_error_campo(item) for item in error.errors()]
    return _respuesta_error(
        422,
        "VALIDATION_ERROR",
        "Los datos enviados no son válidos",
        fields,
    )


async def manejar_error_http(_request: Request, exception: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exception)
    if error.status_code == 404:
        return _respuesta_error(
            404,
            "RESOURCE_NOT_FOUND",
            "El recurso solicitado no existe",
        )
    if error.status_code == 405:
        return _respuesta_error(
            405,
            "METHOD_NOT_ALLOWED",
            "El método HTTP no está permitido para este recurso",
        )

    logger.error("Error HTTP no estandarizado: status=%s", error.status_code)
    return _respuesta_error(
        500,
        "INTERNAL_ERROR",
        "Ocurrió un error interno",
    )


async def manejar_error_interno(request: Request, exception: Exception) -> JSONResponse:
    logger.error(
        "Error inesperado procesando %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return _respuesta_error(
        500,
        "INTERNAL_ERROR",
        "Ocurrió un error interno",
    )


def _respuesta_error(
    status_code: int,
    code: CodigoError,
    message: str,
    fields: list[ErrorCampo] | None = None,
) -> JSONResponse:
    contenido = RespuestaError(code=code, message=message, fields=fields)
    return JSONResponse(status_code=status_code, content=contenido.model_dump(mode="json"))


def _transformar_error_campo(error: dict[str, Any]) -> ErrorCampo:
    return ErrorCampo(
        field=_obtener_nombre_campo(error),
        message=_traducir_mensaje_validacion(error),
    )


def _obtener_nombre_campo(error: dict[str, Any]) -> str:
    ubicacion = list(error.get("loc", ()))
    if ubicacion and ubicacion[0] in {"body", "query", "path", "header", "cookie"}:
        ubicacion.pop(0)
    return ".".join(str(parte) for parte in ubicacion) or "body"


def _traducir_mensaje_validacion(error: dict[str, Any]) -> str:
    tipo = error.get("type")
    contexto = error.get("ctx", {})
    if tipo == "missing":
        return "Campo requerido"
    if tipo == "extra_forbidden":
        return "Campo no permitido"
    if tipo == "greater_than_equal":
        return f"Debe ser mayor o igual a {_formatear_limite(contexto.get('ge'))}"
    if tipo == "less_than_equal":
        return f"Debe ser menor o igual a {_formatear_limite(contexto.get('le'))}"
    if tipo in {"float_parsing", "float_type", "int_parsing", "int_type"}:
        return "Debe ser un número"
    if tipo == "finite_number":
        return "Debe ser un número finito"
    if tipo == "literal_error":
        return "Debe ser uno de los valores permitidos"
    if tipo == "json_invalid":
        return "El cuerpo debe contener JSON válido"
    return "Valor no válido"


def _formatear_limite(valor: object) -> str:
    if isinstance(valor, int | float):
        return f"{valor:g}"
    return str(valor)
