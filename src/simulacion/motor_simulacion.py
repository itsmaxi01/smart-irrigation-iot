# pyright: reportUnnecessaryIsInstance=false

import math

from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import EstadoValvula, Lluvia, Modo, Radiacion, VelocidadRiego


def calcular_secado(
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


def calcular_aporte_lluvia(lluvia: Lluvia) -> float:
    if lluvia == Lluvia.NINGUNA:
        return 0.0
    elif lluvia == Lluvia.LIGERA:
        return 0.30
    elif lluvia == Lluvia.MODERADA:
        return 0.70
    elif lluvia == Lluvia.FUERTE:
        return 1.20

    raise ValueError("Tipo de lluvia no válido")


def calcular_aporte_riego(velocidad: VelocidadRiego) -> float:
    if velocidad == VelocidadRiego.BAJA:
        return 0.50
    elif velocidad == VelocidadRiego.MEDIA:
        return 1.00
    elif velocidad == VelocidadRiego.ALTA:
        return 1.50

    raise ValueError("Velocidad de riego no válida")


def calcular_consumo_agua(velocidad: VelocidadRiego) -> float:
    if velocidad == VelocidadRiego.BAJA:
        return 0.05
    elif velocidad == VelocidadRiego.MEDIA:
        return 0.10
    elif velocidad == VelocidadRiego.ALTA:
        return 0.15

    raise ValueError("Velocidad de riego no válida")


class MotorSimulacion:
    @staticmethod
    def ejecutar_tick(
        dispositivo: DispositivoRiego,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        _validar_ambiente(temperatura, humedad_ambiente, radiacion, lluvia)

        if not isinstance(dispositivo, DispositivoRiego):
            raise ValueError("El dispositivo no es válido")

        _preparar_valvula(dispositivo)

        delta_humedad = (
            _calcular_riego_real(dispositivo)
            + calcular_aporte_lluvia(lluvia)
            - calcular_secado(temperatura, humedad_ambiente, radiacion)
        )
        dispositivo.aplicar_cambio_humedad(delta_humedad)


def _preparar_valvula(dispositivo: DispositivoRiego) -> None:
    if dispositivo.nivel_agua == 0:
        dispositivo.cerrar_valvula()
    elif dispositivo.modo == Modo.AUTOMATICO:
        _actualizar_valvula_automatica(dispositivo)


def _actualizar_valvula_automatica(dispositivo: DispositivoRiego) -> None:
    if dispositivo.humedad_suelo < dispositivo.humedad_minima:
        dispositivo.abrir_valvula()
    elif dispositivo.humedad_suelo >= dispositivo.humedad_objetivo:
        dispositivo.cerrar_valvula()


def _calcular_riego_real(dispositivo: DispositivoRiego) -> float:
    if dispositivo.estado_valvula != EstadoValvula.ABIERTA:
        return 0.0

    consumo_esperado = calcular_consumo_agua(dispositivo.velocidad_riego)
    agua_consumida = dispositivo.consumir_agua(consumo_esperado)
    factor_disponible = agua_consumida / consumo_esperado

    return calcular_aporte_riego(dispositivo.velocidad_riego) * factor_disponible


def _validar_ambiente(
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
