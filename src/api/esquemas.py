from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CambiarModoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modo: Literal["AUTOMATICO", "MANUAL"] = Field(alias="mode")


class CambiarVelocidadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    velocidad: Literal["BAJA", "MEDIA", "ALTA"] = Field(alias="speed")


class CambiarValvulaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["ABIERTA", "CERRADA"] = Field(alias="state")


class EstadoDispositivoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modo: Literal["AUTOMATICO", "MANUAL"] = Field(alias="mode")
    estado_valvula: Literal["ABIERTA", "CERRADA"] = Field(alias="valve")
    velocidad_riego: Literal["BAJA", "MEDIA", "ALTA"] = Field(alias="irrigation_speed")
    humedad_suelo: float = Field(alias="soil_moisture")
    nivel_agua: float = Field(alias="water_level")
    humedad_minima: float = Field(alias="minimum_moisture")
    humedad_objetivo: float = Field(alias="target_moisture")


class CambiarFuenteAmbienteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuente: Literal["MANUAL", "ALEATORIO"] = Field(alias="source")


class FuenteAmbienteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuente: Literal["MANUAL", "ALEATORIO"] = Field(alias="source")


class EstadoAmbienteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuente: Literal["MANUAL", "ALEATORIO"] = Field(alias="source")
    temperatura: float = Field(alias="temperature")
    humedad_ambiente: float = Field(alias="ambient_humidity")
    radiacion: Literal["BAJA", "MEDIA", "ALTA"] = Field(alias="radiation")
    lluvia: Literal["NINGUNA", "LIGERA", "MODERADA", "FUERTE"] = Field(
        alias="rain"
    )


class ActualizarAmbienteManualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    temperatura: float = Field(alias="temperature", ge=-273.15)
    humedad_ambiente: float = Field(alias="ambient_humidity", ge=0, le=100)
    radiacion: Literal["BAJA", "MEDIA", "ALTA"] = Field(alias="radiation")
    lluvia: Literal["NINGUNA", "LIGERA", "MODERADA", "FUERTE"] = Field(
        alias="rain"
    )


class EstadoAmbienteManualResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperatura: float = Field(alias="temperature")
    humedad_ambiente: float = Field(alias="ambient_humidity")
    radiacion: Literal["BAJA", "MEDIA", "ALTA"] = Field(alias="radiation")
    lluvia: Literal["NINGUNA", "LIGERA", "MODERADA", "FUERTE"] = Field(
        alias="rain"
    )
