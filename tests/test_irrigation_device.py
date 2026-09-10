import pytest

from domain.enums import EstadoValvula, Modo, VelocidadRiego
from domain.irrigation_device import IrrigationDevice


def create_device() -> IrrigationDevice:
    return IrrigationDevice(
        modo=Modo.AUTOMATICO,
        velocidad_riego=VelocidadRiego.MEDIA,
        humedad_suelo=40,
        nivel_agua=80,
        humedad_minima=30,
        humedad_objetivo=60,
    )


def test_exposes_device_state_through_read_only_properties() -> None:
    device = create_device()

    assert device.modo == Modo.AUTOMATICO
    assert device.estado_valvula == EstadoValvula.CERRADA
    assert device.velocidad_riego == VelocidadRiego.MEDIA
    assert device.humedad_suelo == 40
    assert device.nivel_agua == 80
    assert device.humedad_minima == 30
    assert device.humedad_objetivo == 60


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("modo", Modo.MANUAL),
        ("estado_valvula", EstadoValvula.ABIERTA),
        ("velocidad_riego", VelocidadRiego.ALTA),
        ("humedad_suelo", 50),
        ("nivel_agua", 50),
        ("humedad_minima", 20),
        ("humedad_objetivo", 70),
    ],
)
def test_prevents_direct_state_changes(attribute: str, value: object) -> None:
    device = create_device()

    with pytest.raises(AttributeError):
        setattr(device, attribute, value)


def test_changes_state_through_domain_operations() -> None:
    device = create_device()

    device.cambiar_modo(Modo.MANUAL)
    device.cambiar_velocidad_riego(VelocidadRiego.ALTA)
    device.abrir_valvula()
    device.aplicar_cambio_humedad(10)
    consumed_water = device.consumir_agua(5)

    assert device.modo == Modo.MANUAL
    assert device.velocidad_riego == VelocidadRiego.ALTA
    assert device.estado_valvula == EstadoValvula.ABIERTA
    assert device.humedad_suelo == 50
    assert device.nivel_agua == 75
    assert consumed_water == 5
