# pyright: reportUnusedFunction=false

from fastapi import APIRouter, HTTPException, status

from api.esquemas import (
    CambiarModoRequest,
    CambiarValvulaRequest,
    CambiarVelocidadRequest,
    EstadoDispositivoResponse,
)
from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.enumeraciones import EstadoValvula, Modo, VelocidadRiego


def _construir_estado_dispositivo(
    servicio_dispositivo: ServicioDispositivo,
) -> EstadoDispositivoResponse:
    (
        modo,
        estado_valvula,
        velocidad_riego,
        humedad_suelo,
        nivel_agua,
        humedad_minima,
        humedad_objetivo,
    ) = servicio_dispositivo.obtener_estado()

    return EstadoDispositivoResponse.model_validate(
        {
            "mode": modo.name,
            "valve": estado_valvula.name,
            "irrigation_speed": velocidad_riego.name,
            "soil_moisture": humedad_suelo,
            "water_level": nivel_agua,
            "minimum_moisture": humedad_minima,
            "target_moisture": humedad_objetivo,
        }
    )


def crear_router(servicio_dispositivo: ServicioDispositivo) -> APIRouter:
    router = APIRouter(prefix="/api/device", tags=["device"])

    @router.get("", response_model=EstadoDispositivoResponse)
    def obtener_dispositivo() -> EstadoDispositivoResponse:
        return _construir_estado_dispositivo(servicio_dispositivo)

    @router.patch("/mode", response_model=EstadoDispositivoResponse)
    def cambiar_modo(solicitud: CambiarModoRequest) -> EstadoDispositivoResponse:
        servicio_dispositivo.cambiar_modo(Modo[solicitud.modo])
        return _construir_estado_dispositivo(servicio_dispositivo)

    @router.patch("/speed", response_model=EstadoDispositivoResponse)
    def cambiar_velocidad(solicitud: CambiarVelocidadRequest) -> EstadoDispositivoResponse:
        servicio_dispositivo.cambiar_velocidad_riego(VelocidadRiego[solicitud.velocidad])
        return _construir_estado_dispositivo(servicio_dispositivo)

    @router.patch("/valve", response_model=EstadoDispositivoResponse)
    def cambiar_valvula(solicitud: CambiarValvulaRequest) -> EstadoDispositivoResponse:
        try:
            if EstadoValvula[solicitud.estado] == EstadoValvula.ABIERTA:
                servicio_dispositivo.abrir_valvula()
            else:
                servicio_dispositivo.cerrar_valvula()
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(error)
            ) from error

        return _construir_estado_dispositivo(servicio_dispositivo)

    return router
