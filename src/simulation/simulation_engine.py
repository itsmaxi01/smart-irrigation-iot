# pyright: reportUnnecessaryIsInstance=false

import math

from domain.enums import EstadoValvula, Lluvia, Modo, Radiacion, VelocidadRiego
from domain.irrigation_device import IrrigationDevice


def calculate_drying(
    temperatura: float,
    humedad_ambiente: float,
    radiacion: Radiacion,
) -> float:
    secado = 0.10

    if temperatura < 20:
        secado += 0.00
    elif temperatura <= 30:
        secado += 0.05
    elif temperatura <= 35:
        secado += 0.10
    else:
        secado += 0.15

    if humedad_ambiente > 70:
        secado += 0.00
    elif humedad_ambiente >= 40:
        secado += 0.05
    else:
        secado += 0.10

    if radiacion == Radiacion.BAJA:
        secado += 0.00
    elif radiacion == Radiacion.MEDIA:
        secado += 0.05
    elif radiacion == Radiacion.ALTA:
        secado += 0.10
    else:
        raise ValueError("Radiación no válida")

    return secado


def calculate_rain_contribution(lluvia: Lluvia) -> float:
    if lluvia == Lluvia.NINGUNA:
        return 0.0
    elif lluvia == Lluvia.LIGERA:
        return 0.30
    elif lluvia == Lluvia.MODERADA:
        return 0.70
    elif lluvia == Lluvia.FUERTE:
        return 1.20

    raise ValueError("Tipo de lluvia no válido")


def calculate_irrigation_contribution(velocidad: VelocidadRiego) -> float:
    if velocidad == VelocidadRiego.BAJA:
        return 0.50
    elif velocidad == VelocidadRiego.MEDIA:
        return 1.00
    elif velocidad == VelocidadRiego.ALTA:
        return 1.50

    raise ValueError("Velocidad de riego no válida")


def calculate_water_consumption(velocidad: VelocidadRiego) -> float:
    if velocidad == VelocidadRiego.BAJA:
        return 0.05
    elif velocidad == VelocidadRiego.MEDIA:
        return 0.10
    elif velocidad == VelocidadRiego.ALTA:
        return 0.15

    raise ValueError("Velocidad de riego no válida")


class SimulationEngine:
    @staticmethod
    def tick(
        device: IrrigationDevice,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        _validate_environment(temperatura, humedad_ambiente, radiacion, lluvia)

        if not isinstance(device, IrrigationDevice):
            raise ValueError("El dispositivo no es válido")

        _prepare_valve(device)

        humidity_delta = (
            _calculate_real_irrigation(device)
            + calculate_rain_contribution(lluvia)
            - calculate_drying(temperatura, humedad_ambiente, radiacion)
        )
        device.aplicar_cambio_humedad(humidity_delta)


def _prepare_valve(device: IrrigationDevice) -> None:
    if device.nivel_agua == 0:
        device.cerrar_valvula()
    elif device.modo == Modo.AUTOMATICO:
        _update_automatic_valve(device)


def _update_automatic_valve(device: IrrigationDevice) -> None:
    if device.humedad_suelo < device.humedad_minima:
        device.abrir_valvula()
    elif device.humedad_suelo >= device.humedad_objetivo:
        device.cerrar_valvula()


def _calculate_real_irrigation(device: IrrigationDevice) -> float:
    if device.estado_valvula != EstadoValvula.ABIERTA:
        return 0.0

    expected_consumption = calculate_water_consumption(device.velocidad_riego)
    consumed_water = device.consumir_agua(expected_consumption)
    available_factor = consumed_water / expected_consumption

    return calculate_irrigation_contribution(device.velocidad_riego) * available_factor


def _validate_environment(
    temperatura: float,
    humedad_ambiente: float,
    radiacion: Radiacion,
    lluvia: Lluvia,
) -> None:
    if not isinstance(temperatura, int | float) or isinstance(temperatura, bool):
        raise ValueError("La temperatura debe ser un número")
    if not math.isfinite(temperatura) or temperatura < -273.15:
        raise ValueError("La temperatura no es físicamente válida")

    if not isinstance(humedad_ambiente, int | float) or isinstance(humedad_ambiente, bool):
        raise ValueError("La humedad ambiente debe ser un número")
    if not math.isfinite(humedad_ambiente) or not 0 <= humedad_ambiente <= 100:
        raise ValueError("La humedad ambiente debe estar entre 0 y 100")

    if not isinstance(radiacion, Radiacion):
        raise ValueError("Radiación no válida")
    if not isinstance(lluvia, Lluvia):
        raise ValueError("Tipo de lluvia no válido")
