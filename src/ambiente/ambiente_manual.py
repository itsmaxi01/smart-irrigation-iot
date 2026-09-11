from dominio.enumeraciones import Lluvia, Radiacion


class AmbienteManual:
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

    def obtener_condiciones(self) -> tuple[float, float, Radiacion, Lluvia]:
        return self._temperatura, self._humedad_ambiente, self._radiacion, self._lluvia

    def actualizar_condiciones(
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
