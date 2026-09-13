# pyright: reportUnusedFunction=false

from fastapi import APIRouter, status

from ambiente.selector_ambiente import SelectorAmbiente
from api.errores import ErrorApi, respuestas_error
from api.esquemas import (
    ActualizarAmbienteManualRequest,
    CambiarFuenteAmbienteRequest,
    EstadoAmbienteManualResponse,
    EstadoAmbienteResponse,
    FuenteAmbienteResponse,
)
from dominio.enumeraciones import FuenteAmbiente, Lluvia, Radiacion


def _construir_respuesta(selector_ambiente: SelectorAmbiente) -> FuenteAmbienteResponse:
    return FuenteAmbienteResponse.model_validate(
        {"source": selector_ambiente.fuente_activa.name}
    )


def _construir_ambiente_manual(
    selector_ambiente: SelectorAmbiente,
) -> EstadoAmbienteManualResponse:
    temperatura, humedad_ambiente, radiacion, lluvia = (
        selector_ambiente.obtener_condiciones_manuales()
    )
    return EstadoAmbienteManualResponse.model_validate(
        {
            "temperature": temperatura,
            "ambient_humidity": humedad_ambiente,
            "radiation": radiacion.name,
            "rain": lluvia.name,
        }
    )


def crear_router(selector_ambiente: SelectorAmbiente) -> APIRouter:
    router = APIRouter(prefix="/api/environment", tags=["environment"])

    @router.get(
        "",
        response_model=EstadoAmbienteResponse,
        responses=respuestas_error(404, 405, 500),
    )
    def obtener_ambiente() -> EstadoAmbienteResponse:
        fuente, condiciones = selector_ambiente.obtener_estado_activo()
        temperatura, humedad_ambiente, radiacion, lluvia = condiciones

        return EstadoAmbienteResponse.model_validate(
            {
                "source": fuente.name,
                "temperature": temperatura,
                "ambient_humidity": humedad_ambiente,
                "radiation": radiacion.name,
                "rain": lluvia.name,
            }
        )

    @router.get(
        "/manual",
        response_model=EstadoAmbienteManualResponse,
        responses=respuestas_error(404, 405, 500),
    )
    def obtener_ambiente_manual() -> EstadoAmbienteManualResponse:
        return _construir_ambiente_manual(selector_ambiente)

    @router.put(
        "/manual",
        response_model=EstadoAmbienteManualResponse,
        responses=respuestas_error(404, 405, 409, 422, 500),
    )
    def actualizar_ambiente_manual(
        solicitud: ActualizarAmbienteManualRequest,
    ) -> EstadoAmbienteManualResponse:
        try:
            selector_ambiente.actualizar_ambiente_manual(
                solicitud.temperatura,
                solicitud.humedad_ambiente,
                Radiacion[solicitud.radiacion],
                Lluvia[solicitud.lluvia],
            )
        except ValueError as error:
            raise ErrorApi(
                status.HTTP_409_CONFLICT,
                "MANUAL_ENVIRONMENT_REQUIRED",
                str(error),
            ) from error

        return _construir_ambiente_manual(selector_ambiente)

    @router.get(
        "/source",
        response_model=FuenteAmbienteResponse,
        responses=respuestas_error(404, 405, 500),
    )
    def obtener_fuente() -> FuenteAmbienteResponse:
        return _construir_respuesta(selector_ambiente)

    @router.patch(
        "/source",
        response_model=FuenteAmbienteResponse,
        responses=respuestas_error(404, 405, 422, 500),
    )
    def cambiar_fuente(
        solicitud: CambiarFuenteAmbienteRequest,
    ) -> FuenteAmbienteResponse:
        selector_ambiente.establecer_fuente_activa(FuenteAmbiente[solicitud.fuente])
        return _construir_respuesta(selector_ambiente)

    return router
