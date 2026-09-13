from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ambiente.ambiente_aleatorio import AmbienteAleatorio
from ambiente.ambiente_manual import AmbienteManual
from ambiente.selector_ambiente import SelectorAmbiente
from api.errores import registrar_manejadores_errores
from api.rutas_ambiente import crear_router as crear_router_ambiente
from api.rutas_dispositivo import crear_router as crear_router_dispositivo
from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import Lluvia, Modo, Radiacion, VelocidadRiego
from mqtt.cliente import ClienteMqtt
from simulacion.ejecutor_simulacion import EjecutorSimulacion

dispositivo = DispositivoRiego(
    modo=Modo.AUTOMATICO,
    velocidad_riego=VelocidadRiego.MEDIA,
    humedad_suelo=42.7,
    nivel_agua=76.4,
    humedad_minima=30,
    humedad_objetivo=60,
)
_bloqueo_dispositivo = Lock()
servicio_dispositivo = ServicioDispositivo(dispositivo, _bloqueo_dispositivo)

ambiente_manual = AmbienteManual(
    temperatura=25,
    humedad_ambiente=50,
    radiacion=Radiacion.MEDIA,
    lluvia=Lluvia.NINGUNA,
)
ambiente_aleatorio = AmbienteAleatorio()
selector_ambiente = SelectorAmbiente(ambiente_manual, ambiente_aleatorio)


def obtener_condiciones_ambiente() -> tuple[float, float, Radiacion, Lluvia]:
    return selector_ambiente.obtener_estado_activo()[1]


cliente_mqtt = ClienteMqtt(servicio_dispositivo, obtener_condiciones_ambiente)
ejecutor_simulacion = EjecutorSimulacion(
    dispositivo,
    selector_ambiente,
    _bloqueo_dispositivo,
    cliente_mqtt.publicar_estado,
)


@asynccontextmanager
async def ciclo_vida(_: FastAPI) -> AsyncGenerator[None]:
    cliente_mqtt.iniciar()
    ejecutor_simulacion.iniciar()
    try:
        yield
    finally:
        ejecutor_simulacion.detener()
        cliente_mqtt.detener()


app = FastAPI(lifespan=ciclo_vida)
registrar_manejadores_errores(app)
app.include_router(crear_router_dispositivo(servicio_dispositivo))
app.include_router(crear_router_ambiente(selector_ambiente))
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True),
    name="frontend",
)
