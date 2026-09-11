from enum import Enum


class Modo(Enum):
    AUTOMATICO = "automatico"
    MANUAL = "manual"


class EstadoValvula(Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"


class VelocidadRiego(Enum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3


class Radiacion(Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class Lluvia(Enum):
    NINGUNA = "ninguna"
    LIGERA = "ligera"
    MODERADA = "moderada"
    FUERTE = "fuerte"


class FuenteAmbiente(Enum):
    MANUAL = "manual"
    ALEATORIO = "aleatorio"
