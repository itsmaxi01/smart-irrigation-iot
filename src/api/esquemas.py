from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from dominio.enumeraciones import EstadoValvula, Modo, VelocidadRiego


def _convertir_nombre_enum[TipoEnum: Enum](valor: object, tipo_enum: type[TipoEnum]) -> object:
    if not isinstance(valor, str):
        return valor

    try:
        return tipo_enum[valor]
    except KeyError as error:
        raise ValueError(f"{valor!r} no es un valor válido") from error


class CambiarModoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modo: Modo = Field(alias="mode")

    @field_validator("modo", mode="before")
    @classmethod
    def convertir_modo(cls, valor: object) -> object:
        return _convertir_nombre_enum(valor, Modo)


class CambiarVelocidadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    velocidad: VelocidadRiego = Field(alias="speed")

    @field_validator("velocidad", mode="before")
    @classmethod
    def convertir_velocidad(cls, valor: object) -> object:
        return _convertir_nombre_enum(valor, VelocidadRiego)


class CambiarValvulaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoValvula = Field(alias="state")

    @field_validator("estado", mode="before")
    @classmethod
    def convertir_estado(cls, valor: object) -> object:
        return _convertir_nombre_enum(valor, EstadoValvula)


class EstadoDispositivoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modo: Modo = Field(alias="mode")
    estado_valvula: EstadoValvula = Field(alias="valve")
    velocidad_riego: VelocidadRiego = Field(alias="irrigation_speed")
    humedad_suelo: float = Field(alias="soil_moisture")
    nivel_agua: float = Field(alias="water_level")
    humedad_minima: float = Field(alias="minimum_moisture")
    humedad_objetivo: float = Field(alias="target_moisture")

    @field_serializer("modo", "estado_valvula", "velocidad_riego")
    def serializar_enum(self, valor: Enum) -> str:
        return valor.name
