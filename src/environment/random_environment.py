from random import Random

from domain.enums import Lluvia, Radiacion

MIN_TEMPERATURE = -10.0
MAX_TEMPERATURE = 45.0
MIN_HUMIDITY = 0.0
MAX_HUMIDITY = 100.0


def generate_random_conditions(
    random_generator: Random | None = None,
) -> tuple[float, float, Radiacion, Lluvia]:
    generator = random_generator if random_generator is not None else Random()

    temperatura = round(generator.uniform(MIN_TEMPERATURE, MAX_TEMPERATURE), 2)
    humedad_ambiente = round(generator.uniform(MIN_HUMIDITY, MAX_HUMIDITY), 2)
    radiacion = generator.choice(tuple(Radiacion))
    lluvia = generator.choice(tuple(Lluvia))

    return temperatura, humedad_ambiente, radiacion, lluvia


class RandomEnvironment:
    def __init__(self, random_generator: Random | None = None) -> None:
        self._random_generator = random_generator if random_generator is not None else Random()

    def get_conditions(self) -> tuple[float, float, Radiacion, Lluvia]:
        return generate_random_conditions(self._random_generator)
