from time import sleep

from domain.irrigation_device import IrrigationDevice
from environment.environment_selector import EnvironmentSelector
from simulation.simulation_engine import SimulationEngine

TICK_INTERVAL_SECONDS = 1.0


class SimulationRunner:
    def __init__(
        self,
        device: IrrigationDevice,
        environment_selector: EnvironmentSelector,
    ) -> None:
        self._device = device
        self._environment_selector = environment_selector
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    def run(self) -> None:
        self._is_active = True

        while self._is_active:
            environment = self._environment_selector.get_active_environment()
            conditions = environment.get_conditions()
            SimulationEngine.tick(self._device, *conditions)
            sleep(TICK_INTERVAL_SECONDS)

    def stop(self) -> None:
        self._is_active = False
