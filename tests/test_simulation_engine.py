import pytest

from domain.enums import EstadoValvula, Lluvia, Modo, Radiacion, VelocidadRiego
from domain.irrigation_device import IrrigationDevice
from simulation.simulation_engine import (
    SimulationEngine,
    calculate_drying,
    calculate_irrigation_contribution,
    calculate_rain_contribution,
    calculate_water_consumption,
)


def create_device(
    *,
    modo: Modo = Modo.MANUAL,
    velocidad: VelocidadRiego = VelocidadRiego.MEDIA,
    humedad: float = 50,
    agua: float = 100,
    minima: float = 30,
    objetivo: float = 60,
) -> IrrigationDevice:
    return IrrigationDevice(modo, velocidad, humedad, agua, minima, objetivo)


def run_tick(device: IrrigationDevice, *, lluvia: Lluvia = Lluvia.NINGUNA) -> None:
    SimulationEngine.tick(device, 19, 80, Radiacion.BAJA, lluvia)


@pytest.mark.parametrize(
    ("temperatura", "humedad_ambiente", "radiacion", "expected"),
    [
        (19, 71, Radiacion.BAJA, 0.10),
        (20, 70, Radiacion.MEDIA, 0.25),
        (31, 39, Radiacion.ALTA, 0.40),
        (36, 80, Radiacion.BAJA, 0.25),
    ],
)
def test_calculate_drying(
    temperatura: float,
    humedad_ambiente: float,
    radiacion: Radiacion,
    expected: float,
) -> None:
    assert calculate_drying(temperatura, humedad_ambiente, radiacion) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("lluvia", "expected"),
    [
        (Lluvia.NINGUNA, 0.0),
        (Lluvia.LIGERA, 0.30),
        (Lluvia.MODERADA, 0.70),
        (Lluvia.FUERTE, 1.20),
    ],
)
def test_calculate_rain_contribution(lluvia: Lluvia, expected: float) -> None:
    assert calculate_rain_contribution(lluvia) == expected


@pytest.mark.parametrize(
    ("velocidad", "expected"),
    [
        (VelocidadRiego.BAJA, 0.50),
        (VelocidadRiego.MEDIA, 1.00),
        (VelocidadRiego.ALTA, 1.50),
    ],
)
def test_calculate_irrigation_contribution(velocidad: VelocidadRiego, expected: float) -> None:
    assert calculate_irrigation_contribution(velocidad) == expected


@pytest.mark.parametrize(
    ("velocidad", "expected"),
    [
        (VelocidadRiego.BAJA, 0.05),
        (VelocidadRiego.MEDIA, 0.10),
        (VelocidadRiego.ALTA, 0.15),
    ],
)
def test_calculate_water_consumption(velocidad: VelocidadRiego, expected: float) -> None:
    assert calculate_water_consumption(velocidad) == expected


def test_automatic_mode_opens_below_minimum() -> None:
    device = create_device(modo=Modo.AUTOMATICO, humedad=29)

    run_tick(device)

    assert device.estado_valvula == EstadoValvula.ABIERTA


def test_automatic_mode_closes_at_target() -> None:
    device = create_device(modo=Modo.AUTOMATICO, humedad=60)
    device.abrir_valvula()

    run_tick(device)

    assert device.estado_valvula == EstadoValvula.CERRADA


@pytest.mark.parametrize("initial_state", [EstadoValvula.ABIERTA, EstadoValvula.CERRADA])
def test_automatic_mode_maintains_valve_between_thresholds(
    initial_state: EstadoValvula,
) -> None:
    device = create_device(modo=Modo.AUTOMATICO, humedad=45)
    if initial_state == EstadoValvula.ABIERTA:
        device.abrir_valvula()

    run_tick(device)

    assert device.estado_valvula == initial_state


@pytest.mark.parametrize("initial_state", [EstadoValvula.ABIERTA, EstadoValvula.CERRADA])
def test_manual_mode_does_not_change_valve_automatically(
    initial_state: EstadoValvula,
) -> None:
    device = create_device(modo=Modo.MANUAL, humedad=70)
    if initial_state == EstadoValvula.ABIERTA:
        device.abrir_valvula()

    run_tick(device)

    assert device.estado_valvula == initial_state


def test_open_valve_increases_humidity_and_consumes_water() -> None:
    device = create_device(velocidad=VelocidadRiego.MEDIA)
    device.abrir_valvula()

    run_tick(device)

    assert device.humedad_suelo == pytest.approx(50.90)
    assert device.nivel_agua == pytest.approx(99.90)


def test_closed_valve_allows_environment_to_dry_soil() -> None:
    device = create_device(humedad=50)

    run_tick(device)

    assert device.humedad_suelo == pytest.approx(49.90)


def test_rain_increases_humidity() -> None:
    device = create_device(humedad=50)

    run_tick(device, lluvia=Lluvia.MODERADA)

    assert device.humedad_suelo == pytest.approx(50.60)


def test_empty_tank_prevents_irrigation() -> None:
    device = create_device(modo=Modo.AUTOMATICO, humedad=20, agua=0)

    run_tick(device)

    assert device.estado_valvula == EstadoValvula.CERRADA
    assert device.nivel_agua == 0
    assert device.humedad_suelo == pytest.approx(19.90)


def test_tank_that_empties_during_tick_closes_valve() -> None:
    device = create_device(velocidad=VelocidadRiego.ALTA, agua=0.15)
    device.abrir_valvula()

    run_tick(device)

    assert device.nivel_agua == 0
    assert device.estado_valvula == EstadoValvula.CERRADA


def test_insufficient_water_produces_proportional_irrigation() -> None:
    device = create_device(velocidad=VelocidadRiego.ALTA, humedad=50, agua=0.03)
    device.abrir_valvula()

    run_tick(device)

    assert device.humedad_suelo == pytest.approx(50.20)
    assert device.nivel_agua == 0
    assert device.estado_valvula == EstadoValvula.CERRADA


def test_humidity_never_exceeds_one_hundred() -> None:
    device = create_device(humedad=99.9)

    run_tick(device, lluvia=Lluvia.FUERTE)

    assert device.humedad_suelo == 100


def test_humidity_never_goes_below_zero() -> None:
    device = create_device(humedad=0)

    run_tick(device)

    assert device.humedad_suelo == 0


@pytest.mark.parametrize(
    ("temperatura", "humedad_ambiente", "radiacion", "lluvia"),
    [
        (float("nan"), 50, Radiacion.BAJA, Lluvia.NINGUNA),
        (-274, 50, Radiacion.BAJA, Lluvia.NINGUNA),
        (25, -1, Radiacion.BAJA, Lluvia.NINGUNA),
        (25, 101, Radiacion.BAJA, Lluvia.NINGUNA),
        (25, 50, "baja", Lluvia.NINGUNA),
        (25, 50, Radiacion.BAJA, "ninguna"),
    ],
)
def test_tick_rejects_impossible_environment_values(
    temperatura: float,
    humedad_ambiente: float,
    radiacion: object,
    lluvia: object,
) -> None:
    device = create_device()

    with pytest.raises(ValueError):
        SimulationEngine.tick(  # type: ignore[arg-type]
            device, temperatura, humedad_ambiente, radiacion, lluvia
        )
