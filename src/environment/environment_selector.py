# pyright: reportUnnecessaryIsInstance=false

from domain.enums import EnvironmentSource
from environment.manual_environment import ManualEnvironment
from environment.random_environment import RandomEnvironment


class EnvironmentSelector:
    def __init__(
        self,
        manual_environment: ManualEnvironment,
        random_environment: RandomEnvironment,
    ) -> None:
        self._manual_environment = manual_environment
        self._random_environment = random_environment
        self._active_source = EnvironmentSource.RANDOM

    @property
    def active_source(self) -> EnvironmentSource:
        return self._active_source

    def set_active_source(self, source: EnvironmentSource) -> None:
        if not isinstance(source, EnvironmentSource):
            raise ValueError("Fuente de ambiente no válida")

        self._active_source = source

    def get_active_environment(self) -> ManualEnvironment | RandomEnvironment:
        if self._active_source == EnvironmentSource.MANUAL:
            return self._manual_environment

        if self._active_source == EnvironmentSource.RANDOM:
            return self._random_environment

        raise ValueError("Fuente de ambiente no válida")
