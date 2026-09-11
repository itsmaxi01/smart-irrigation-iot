from random import Random

from ambiente.ambiente_aleatorio import (
    HUMEDAD_MAXIMA,
    HUMEDAD_MINIMA,
    TEMPERATURA_MAXIMA,
    TEMPERATURA_MINIMA,
    generar_condiciones_aleatorias,
)
from dominio.enumeraciones import Lluvia, Radiacion


def test_ambiente_aleatorio_es_reproducible_con_semilla() -> None:
    primeras_condiciones = generar_condiciones_aleatorias(Random(42))
    segundas_condiciones = generar_condiciones_aleatorias(Random(42))

    assert primeras_condiciones == segundas_condiciones


def test_ambiente_aleatorio_devuelve_condiciones_validas() -> None:
    temperatura, humedad_ambiente, radiacion, lluvia = generar_condiciones_aleatorias(Random(7))

    assert TEMPERATURA_MINIMA <= temperatura <= TEMPERATURA_MAXIMA
    assert HUMEDAD_MINIMA <= humedad_ambiente <= HUMEDAD_MAXIMA
    assert isinstance(radiacion, Radiacion)
    assert isinstance(lluvia, Lluvia)
