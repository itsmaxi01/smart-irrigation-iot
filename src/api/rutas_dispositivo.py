# pyright: reportUnusedFunction=false

from fastapi import APIRouter, HTTPException, status

from api.esquemas import (
    CambiarModoRequest,
    CambiarValvulaRequest,
    CambiarVelocidadRequest,
    EstadoDispositivoResponse,
)
from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import EstadoValvula


def _construir_estado_dispositivo(
    dispositivo: DispositivoRiego,
) -> EstadoDispositivoResponse:
    return EstadoDispositivoResponse.model_validate(
        {
            "mode": dispositivo.modo,
            "valve": dispositivo.estado_valvula,
            "irrigation_speed": dispositivo.velocidad_riego,
            "soil_moisture": dispositivo.humedad_suelo,
            "water_level": dispositivo.nivel_agua,
            "minimum_moisture": dispositivo.humedad_minima,
            "target_moisture": dispositivo.humedad_objetivo,
        }
    )


def crear_router(servicio_dispositivo: ServicioDispositivo) -> APIRouter:
    router = APIRouter(prefix="/api/device", tags=["device"])
    dispositivo = servicio_dispositivo.dispositivo

    @router.get("", response_model=EstadoDispositivoResponse)
    def obtener_dispositivo() -> EstadoDispositivoResponse:
        return _construir_estado_dispositivo(dispositivo)

    @router.patch("/mode", response_model=EstadoDispositivoResponse)
    def cambiar_modo(solicitud: CambiarModoRequest) -> EstadoDispositivoResponse:
        servicio_dispositivo.cambiar_modo(solicitud.modo)
        return _construir_estado_dispositivo(dispositivo)

    @router.patch("/speed", response_model=EstadoDispositivoResponse)
    def cambiar_velocidad(solicitud: CambiarVelocidadRequest) -> EstadoDispositivoResponse:
        servicio_dispositivo.cambiar_velocidad_riego(solicitud.velocidad)
        return _construir_estado_dispositivo(dispositivo)

    @router.patch("/valve", response_model=EstadoDispositivoResponse)
    def cambiar_valvula(solicitud: CambiarValvulaRequest) -> EstadoDispositivoResponse:
        try:
            if solicitud.estado == EstadoValvula.ABIERTA:
                servicio_dispositivo.abrir_valvula()
            else:
                servicio_dispositivo.cerrar_valvula()
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(error)
            ) from error

        return _construir_estado_dispositivo(dispositivo)

    return router
