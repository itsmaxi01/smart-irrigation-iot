from fastapi import FastAPI

from api.rutas_dispositivo import crear_router
from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import Modo, VelocidadRiego

dispositivo = DispositivoRiego(
    modo=Modo.AUTOMATICO,
    velocidad_riego=VelocidadRiego.MEDIA,
    humedad_suelo=42.7,
    nivel_agua=76.4,
    humedad_minima=30,
    humedad_objetivo=60,
)
servicio_dispositivo = ServicioDispositivo(dispositivo)

app = FastAPI()
app.include_router(crear_router(servicio_dispositivo))
