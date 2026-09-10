from domain.enums import Lluvia, Radiacion


class ManualEnvironment:
    def __init__(
        self,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        self._temperatura = temperatura
        self._humedad_ambiente = humedad_ambiente
        self._radiacion = radiacion
        self._lluvia = lluvia

    def get_conditions(self) -> tuple[float, float, Radiacion, Lluvia]:
        return self._temperatura, self._humedad_ambiente, self._radiacion, self._lluvia

    def update_conditions(
        self,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        self._temperatura = temperatura
        self._humedad_ambiente = humedad_ambiente
        self._radiacion = radiacion
        self._lluvia = lluvia
