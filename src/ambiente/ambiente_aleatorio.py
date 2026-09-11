from random import Random

from dominio.enumeraciones import Lluvia, Radiacion

TEMPERATURA_MINIMA = -10.0
TEMPERATURA_MAXIMA = 45.0
HUMEDAD_MINIMA = 0.0
HUMEDAD_MAXIMA = 100.0


def generar_condiciones_aleatorias(
    generador_aleatorio: Random | None = None,
) -> tuple[float, float, Radiacion, Lluvia]:
    generador = generador_aleatorio if generador_aleatorio is not None else Random()

    temperatura = round(generador.uniform(TEMPERATURA_MINIMA, TEMPERATURA_MAXIMA), 2)
    humedad_ambiente = round(generador.uniform(HUMEDAD_MINIMA, HUMEDAD_MAXIMA), 2)
    radiacion = generador.choice(tuple(Radiacion))
    lluvia = generador.choice(tuple(Lluvia))

    return temperatura, humedad_ambiente, radiacion, lluvia


class AmbienteAleatorio:
    def __init__(self, generador_aleatorio: Random | None = None) -> None:
        self._generador_aleatorio = (
            generador_aleatorio if generador_aleatorio is not None else Random()
        )

    def obtener_condiciones(self) -> tuple[float, float, Radiacion, Lluvia]:
        return generar_condiciones_aleatorias(self._generador_aleatorio)
