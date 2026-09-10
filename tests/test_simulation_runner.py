from random import Random

import pytest

from domain.enums import EnvironmentSource, Lluvia, Modo, Radiacion, VelocidadRiego
from domain.irrigation_device import IrrigationDevice
from environment.environment_selector import EnvironmentSelector
from environment.manual_environment import ManualEnvironment
from environment.random_environment import RandomEnvironment
from simulation.simulation_runner import SimulationRunner


def create_device() -> IrrigationDevice:
    return IrrigationDevice(
        modo=Modo.MANUAL,
        velocidad_riego=VelocidadRiego.MEDIA,
        humedad_suelo=50,
        nivel_agua=100,
        humedad_minima=30,
        humedad_objetivo=60,
    )


def create_selector() -> EnvironmentSelector:
    manual_environment = ManualEnvironment(19, 80, Radiacion.BAJA, Lluvia.NINGUNA)
    random_environment = RandomEnvironment(Random(42))
    return EnvironmentSelector(manual_environment, random_environment)


def test_selector_returns_externally_selected_environment() -> None:
    selector = create_selector()

    assert isinstance(selector.get_active_environment(), RandomEnvironment)

    selector.set_active_source(EnvironmentSource.MANUAL)

    assert isinstance(selector.get_active_environment(), ManualEnvironment)


def test_manual_environment_returns_and_updates_current_conditions() -> None:
    environment = ManualEnvironment(20, 50, Radiacion.MEDIA, Lluvia.LIGERA)

    environment.update_conditions(30, 70, Radiacion.ALTA, Lluvia.FUERTE)

    assert environment.get_conditions() == (30, 70, Radiacion.ALTA, Lluvia.FUERTE)


def test_runner_ticks_then_waits_one_second(monkeypatch: pytest.MonkeyPatch) -> None:
    device = create_device()
    selector = create_selector()
    selector.set_active_source(EnvironmentSource.MANUAL)
    runner = SimulationRunner(device, selector)
    waits: list[float] = []

    def stop_after_wait(seconds: float) -> None:
        waits.append(seconds)
        runner.stop()

    monkeypatch.setattr("simulation.simulation_runner.sleep", stop_after_wait)

    runner.run()

    assert device.humedad_suelo == pytest.approx(49.90)
    assert waits == [1.0]
    assert runner.is_active is False
    assert selector.active_source == EnvironmentSource.MANUAL


def test_runner_reads_active_source_on_each_iteration(monkeypatch: pytest.MonkeyPatch) -> None:
    device = create_device()
    selector = create_selector()
    runner = SimulationRunner(device, selector)
    executed_ticks = 0
    used_sources: list[EnvironmentSource] = []

    def random_conditions() -> tuple[float, float, Radiacion, Lluvia]:
        used_sources.append(EnvironmentSource.RANDOM)
        return 19, 80, Radiacion.BAJA, Lluvia.NINGUNA

    def manual_conditions() -> tuple[float, float, Radiacion, Lluvia]:
        used_sources.append(EnvironmentSource.MANUAL)
        return 19, 80, Radiacion.BAJA, Lluvia.NINGUNA

    random_environment = selector.get_active_environment()
    selector.set_active_source(EnvironmentSource.MANUAL)
    manual_environment = selector.get_active_environment()
    selector.set_active_source(EnvironmentSource.RANDOM)

    def switch_source_then_stop(_: float) -> None:
        nonlocal executed_ticks
        executed_ticks += 1
        if executed_ticks == 1:
            selector.set_active_source(EnvironmentSource.MANUAL)
        else:
            runner.stop()

    monkeypatch.setattr("simulation.simulation_runner.sleep", switch_source_then_stop)
    monkeypatch.setattr(random_environment, "get_conditions", random_conditions)
    monkeypatch.setattr(manual_environment, "get_conditions", manual_conditions)

    runner.run()

    assert executed_ticks == 2
    assert used_sources == [EnvironmentSource.RANDOM, EnvironmentSource.MANUAL]
    assert selector.active_source == EnvironmentSource.MANUAL
