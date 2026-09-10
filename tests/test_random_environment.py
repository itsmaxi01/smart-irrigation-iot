from random import Random

from domain.enums import Lluvia, Radiacion
from environment.random_environment import (
    MAX_HUMIDITY,
    MAX_TEMPERATURE,
    MIN_HUMIDITY,
    MIN_TEMPERATURE,
    generate_random_conditions,
)


def test_random_environment_is_reproducible_with_a_seed() -> None:
    first_conditions = generate_random_conditions(Random(42))
    second_conditions = generate_random_conditions(Random(42))

    assert first_conditions == second_conditions


def test_random_environment_returns_valid_conditions() -> None:
    temperatura, humedad_ambiente, radiacion, lluvia = generate_random_conditions(Random(7))

    assert MIN_TEMPERATURE <= temperatura <= MAX_TEMPERATURE
    assert MIN_HUMIDITY <= humedad_ambiente <= MAX_HUMIDITY
    assert isinstance(radiacion, Radiacion)
    assert isinstance(lluvia, Lluvia)
