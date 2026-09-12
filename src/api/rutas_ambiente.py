# pyright: reportUnusedFunction=false

from fastapi import APIRouter

from ambiente.selector_ambiente import SelectorAmbiente
from api.esquemas import (
    CambiarFuenteAmbienteRequest,
    EstadoAmbienteResponse,
    FuenteAmbienteResponse,
)
from dominio.enumeraciones import FuenteAmbiente


def _construir_respuesta(selector_ambiente: SelectorAmbiente) -> FuenteAmbienteResponse:
    return FuenteAmbienteResponse.model_validate(
        {"source": selector_ambiente.fuente_activa.name}
    )


def crear_router(selector_ambiente: SelectorAmbiente) -> APIRouter:
    router = APIRouter(prefix="/api/environment", tags=["environment"])

    @router.get("", response_model=EstadoAmbienteResponse)
    def obtener_ambiente() -> EstadoAmbienteResponse:
        ambiente = selector_ambiente.obtener_ambiente_activo()
        temperatura, humedad_ambiente, radiacion, lluvia = (
            ambiente.obtener_condiciones()
        )

        return EstadoAmbienteResponse.model_validate(
            {
                "source": selector_ambiente.fuente_activa.name,
                "temperature": temperatura,
                "ambient_humidity": humedad_ambiente,
                "radiation": radiacion.name,
                "rain": lluvia.name,
            }
        )

    @router.get("/source", response_model=FuenteAmbienteResponse)
    def obtener_fuente() -> FuenteAmbienteResponse:
        return _construir_respuesta(selector_ambiente)

    @router.patch("/source", response_model=FuenteAmbienteResponse)
    def cambiar_fuente(
        solicitud: CambiarFuenteAmbienteRequest,
    ) -> FuenteAmbienteResponse:
        selector_ambiente.establecer_fuente_activa(FuenteAmbiente[solicitud.fuente])
        return _construir_respuesta(selector_ambiente)

    return router
