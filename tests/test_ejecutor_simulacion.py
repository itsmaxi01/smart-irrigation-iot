from random import Random

import pytest

from ambiente.ambiente_aleatorio import AmbienteAleatorio
from ambiente.ambiente_manual import AmbienteManual
from ambiente.selector_ambiente import SelectorAmbiente
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import (
    FuenteAmbiente,
    Lluvia,
    Modo,
    Radiacion,
    VelocidadRiego,
)
from simulacion.ejecutor_simulacion import EjecutorSimulacion


def crear_dispositivo() -> DispositivoRiego:
    return DispositivoRiego(
        modo=Modo.MANUAL,
        velocidad_riego=VelocidadRiego.MEDIA,
        humedad_suelo=50,
        nivel_agua=100,
        humedad_minima=30,
        humedad_objetivo=60,
    )


def crear_selector() -> SelectorAmbiente:
    ambiente_manual = AmbienteManual(19, 80, Radiacion.BAJA, Lluvia.NINGUNA)
    ambiente_aleatorio = AmbienteAleatorio(Random(42))
    return SelectorAmbiente(ambiente_manual, ambiente_aleatorio)


def test_selector_devuelve_ambiente_seleccionado_externamente() -> None:
    selector = crear_selector()

    assert isinstance(selector.obtener_ambiente_activo(), AmbienteAleatorio)

    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)

    assert isinstance(selector.obtener_ambiente_activo(), AmbienteManual)


def test_ambiente_manual_devuelve_y_actualiza_condiciones() -> None:
    ambiente = AmbienteManual(20, 50, Radiacion.MEDIA, Lluvia.LIGERA)

    ambiente.actualizar_condiciones(30, 70, Radiacion.ALTA, Lluvia.FUERTE)

    assert ambiente.obtener_condiciones() == (30, 70, Radiacion.ALTA, Lluvia.FUERTE)


def test_ejecutor_ejecuta_tick_y_luego_espera_un_segundo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    ejecutor = EjecutorSimulacion(dispositivo, selector)
    esperas: list[float] = []

    def detener_despues_de_esperar(segundos: float) -> None:
        esperas.append(segundos)
        ejecutor.detener()

    monkeypatch.setattr("simulacion.ejecutor_simulacion.dormir", detener_despues_de_esperar)

    ejecutor.ejecutar()

    assert dispositivo.humedad_suelo == pytest.approx(49.90)
    assert esperas == [1.0]
    assert ejecutor.activo is False
    assert selector.fuente_activa == FuenteAmbiente.MANUAL


def test_ejecutor_lee_fuente_activa_en_cada_iteracion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    ejecutor = EjecutorSimulacion(dispositivo, selector)
    ticks_ejecutados = 0
    fuentes_usadas: list[FuenteAmbiente] = []

    def condiciones_aleatorias() -> tuple[float, float, Radiacion, Lluvia]:
        fuentes_usadas.append(FuenteAmbiente.ALEATORIO)
        return 19, 80, Radiacion.BAJA, Lluvia.NINGUNA

    def condiciones_manuales() -> tuple[float, float, Radiacion, Lluvia]:
        fuentes_usadas.append(FuenteAmbiente.MANUAL)
        return 19, 80, Radiacion.BAJA, Lluvia.NINGUNA

    ambiente_aleatorio = selector.obtener_ambiente_activo()
    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    ambiente_manual = selector.obtener_ambiente_activo()
    selector.establecer_fuente_activa(FuenteAmbiente.ALEATORIO)

    def cambiar_fuente_y_detener(_: float) -> None:
        nonlocal ticks_ejecutados
        ticks_ejecutados += 1
        if ticks_ejecutados == 1:
            selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
        else:
            ejecutor.detener()

    monkeypatch.setattr("simulacion.ejecutor_simulacion.dormir", cambiar_fuente_y_detener)
    monkeypatch.setattr(ambiente_aleatorio, "obtener_condiciones", condiciones_aleatorias)
    monkeypatch.setattr(ambiente_manual, "obtener_condiciones", condiciones_manuales)

    ejecutor.ejecutar()

    assert ticks_ejecutados == 2
    assert fuentes_usadas == [FuenteAmbiente.ALEATORIO, FuenteAmbiente.MANUAL]
    assert selector.fuente_activa == FuenteAmbiente.MANUAL
