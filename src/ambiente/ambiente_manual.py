from dominio.enumeraciones import Lluvia, Radiacion


class AmbienteManual:
    def __init__(
        self,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        self._condiciones = (temperatura, humedad_ambiente, radiacion, lluvia)

    def obtener_condiciones(self) -> tuple[float, float, Radiacion, Lluvia]:
        return self._condiciones

    def actualizar_condiciones(
        self,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        self._condiciones = (temperatura, humedad_ambiente, radiacion, lluvia)
