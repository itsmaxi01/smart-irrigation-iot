from collections.abc import Callable
from random import Random
from threading import Event, Lock, Thread

import pytest

from ambiente.ambiente_aleatorio import AmbienteAleatorio
from ambiente.ambiente_manual import AmbienteManual
from ambiente.selector_ambiente import SelectorAmbiente
from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import (
    EstadoValvula,
    FuenteAmbiente,
    Lluvia,
    Modo,
    Radiacion,
    VelocidadRiego,
)
from simulacion.ejecutor_simulacion import EjecutorSimulacion
from simulacion.motor_simulacion import MotorSimulacion


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


def test_selector_no_intercala_lectura_y_actualizacion_del_ambiente_manual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selector = crear_selector()
    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    ambiente = selector.obtener_ambiente_activo()
    assert isinstance(ambiente, AmbienteManual)
    obtener_condiciones_original = ambiente.obtener_condiciones
    lectura_iniciada = Event()
    permitir_lectura = Event()
    actualizacion_terminada = Event()
    estados: list[
        tuple[FuenteAmbiente, tuple[float, float, Radiacion, Lluvia]]
    ] = []

    def obtener_condiciones_controladas() -> tuple[float, float, Radiacion, Lluvia]:
        lectura_iniciada.set()
        permitir_lectura.wait(1)
        return obtener_condiciones_original()

    def leer_estado() -> None:
        estados.append(selector.obtener_estado_activo())

    def actualizar_ambiente() -> None:
        selector.actualizar_ambiente_manual(
            30,
            70,
            Radiacion.ALTA,
            Lluvia.FUERTE,
        )
        actualizacion_terminada.set()

    monkeypatch.setattr(ambiente, "obtener_condiciones", obtener_condiciones_controladas)
    hilo_lectura = Thread(target=leer_estado)
    hilo_actualizacion = Thread(target=actualizar_ambiente)
    hilo_lectura.start()
    assert lectura_iniciada.wait(1)
    hilo_actualizacion.start()
    assert not actualizacion_terminada.wait(0.05)

    permitir_lectura.set()
    hilo_lectura.join()
    hilo_actualizacion.join()

    assert estados == [
        (FuenteAmbiente.MANUAL, (19, 80, Radiacion.BAJA, Lluvia.NINGUNA))
    ]
    assert selector.obtener_condiciones_manuales() == (
        30,
        70,
        Radiacion.ALTA,
        Lluvia.FUERTE,
    )


def test_iniciar_ejecuta_ticks_automaticamente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    ejecutor = EjecutorSimulacion(dispositivo, selector, Lock())
    tick_ejecutado = Event()

    def registrar_tick(
        dispositivo: DispositivoRiego,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        tick_ejecutado.set()

    monkeypatch.setattr(MotorSimulacion, "ejecutar_tick", staticmethod(registrar_tick))

    ejecutor.iniciar()
    try:
        assert tick_ejecutado.wait(1)
    finally:
        ejecutor.detener()

    assert ejecutor.activo is False


def test_detener_impide_nuevos_ticks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    ejecutor = EjecutorSimulacion(dispositivo, selector, Lock())
    tick_ejecutado = Event()
    ticks: list[None] = []

    def registrar_tick(
        dispositivo: DispositivoRiego,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        ticks.append(None)
        tick_ejecutado.set()

    monkeypatch.setattr(MotorSimulacion, "ejecutar_tick", staticmethod(registrar_tick))

    ejecutor.iniciar()
    assert tick_ejecutado.wait(1)
    ejecutor.detener()
    ticks_al_detener = len(ticks)

    Event().wait(0.05)

    assert len(ticks) == ticks_al_detener
    assert ejecutor.activo is False


def test_iniciar_dos_veces_crea_un_solo_hilo(monkeypatch: pytest.MonkeyPatch) -> None:
    class HiloFalso:
        def __init__(
            self,
            *,
            target: Callable[[], None],
            name: str,
            daemon: bool,
        ) -> None:
            self._activo = False
            hilos_creados.append(self)

        def start(self) -> None:
            self._activo = True

        def is_alive(self) -> bool:
            return self._activo

        def join(self) -> None:
            self._activo = False

    hilos_creados: list[HiloFalso] = []

    monkeypatch.setattr("simulacion.ejecutor_simulacion.Thread", HiloFalso)
    ejecutor = EjecutorSimulacion(crear_dispositivo(), crear_selector(), Lock())

    ejecutor.iniciar()
    ejecutor.iniciar()

    assert len(hilos_creados) == 1
    ejecutor.detener()


def test_ejecutor_lee_fuente_activa_en_cada_iteracion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    ejecutor = EjecutorSimulacion(dispositivo, selector, Lock())
    fuentes_usadas: list[FuenteAmbiente] = []
    segundo_tick = Event()

    ambiente_aleatorio = selector.obtener_ambiente_activo()
    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    ambiente_manual = selector.obtener_ambiente_activo()
    selector.establecer_fuente_activa(FuenteAmbiente.ALEATORIO)

    def condiciones_aleatorias() -> tuple[float, float, Radiacion, Lluvia]:
        fuentes_usadas.append(FuenteAmbiente.ALEATORIO)
        return 19, 80, Radiacion.BAJA, Lluvia.NINGUNA

    def condiciones_manuales() -> tuple[float, float, Radiacion, Lluvia]:
        fuentes_usadas.append(FuenteAmbiente.MANUAL)
        return 19, 80, Radiacion.BAJA, Lluvia.NINGUNA

    def registrar_tick(
        dispositivo: DispositivoRiego,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        if len(fuentes_usadas) == 1:
            selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
        else:
            segundo_tick.set()

    monkeypatch.setattr(ambiente_aleatorio, "obtener_condiciones", condiciones_aleatorias)
    monkeypatch.setattr(ambiente_manual, "obtener_condiciones", condiciones_manuales)
    monkeypatch.setattr(MotorSimulacion, "ejecutar_tick", staticmethod(registrar_tick))
    monkeypatch.setattr("simulacion.ejecutor_simulacion.INTERVALO_TICK_SEGUNDOS", 0.01)

    ejecutor.iniciar()
    try:
        assert segundo_tick.wait(2)
    finally:
        ejecutor.detener()

    assert fuentes_usadas == [FuenteAmbiente.ALEATORIO, FuenteAmbiente.MANUAL]


def test_comando_externo_no_se_intercala_durante_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    bloqueo_dispositivo = Lock()
    servicio = ServicioDispositivo(dispositivo, bloqueo_dispositivo)
    ejecutor = EjecutorSimulacion(dispositivo, selector, bloqueo_dispositivo)
    tick_iniciado = Event()
    completar_tick = Event()
    comando_iniciado = Event()
    comando_terminado = Event()
    velocidades_observadas: list[VelocidadRiego] = []

    def tick_controlado(
        dispositivo: DispositivoRiego,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        velocidades_observadas.append(dispositivo.velocidad_riego)
        tick_iniciado.set()
        completar_tick.wait(1)
        velocidades_observadas.append(dispositivo.velocidad_riego)

    def cambiar_velocidad() -> None:
        comando_iniciado.set()
        servicio.cambiar_velocidad_riego(VelocidadRiego.ALTA)
        comando_terminado.set()

    monkeypatch.setattr(MotorSimulacion, "ejecutar_tick", staticmethod(tick_controlado))
    ejecutor.iniciar()
    assert tick_iniciado.wait(1)

    hilo_comando = Thread(target=cambiar_velocidad)
    hilo_comando.start()
    assert comando_iniciado.wait(1)
    assert not comando_terminado.wait(0.05)

    completar_tick.set()
    assert comando_terminado.wait(1)
    hilo_comando.join()
    ejecutor.detener()

    assert velocidades_observadas == [VelocidadRiego.MEDIA, VelocidadRiego.MEDIA]
    assert dispositivo.velocidad_riego == VelocidadRiego.ALTA


def test_lectura_obtiene_estado_completo_despues_del_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    bloqueo_dispositivo = Lock()
    servicio = ServicioDispositivo(dispositivo, bloqueo_dispositivo)
    ejecutor = EjecutorSimulacion(dispositivo, selector, bloqueo_dispositivo)
    mitad_tick = Event()
    completar_tick = Event()
    lectura_iniciada = Event()
    lectura_terminada = Event()
    estados: list[
        tuple[Modo, EstadoValvula, VelocidadRiego, float, float, float, float]
    ] = []

    def tick_controlado(
        dispositivo: DispositivoRiego,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        dispositivo.aplicar_cambio_humedad(10)
        mitad_tick.set()
        completar_tick.wait(1)
        dispositivo.consumir_agua(5)

    def leer_estado() -> None:
        lectura_iniciada.set()
        estados.append(servicio.obtener_estado())
        lectura_terminada.set()

    monkeypatch.setattr(MotorSimulacion, "ejecutar_tick", staticmethod(tick_controlado))
    ejecutor.iniciar()
    assert mitad_tick.wait(1)

    hilo_lectura = Thread(target=leer_estado)
    hilo_lectura.start()
    assert lectura_iniciada.wait(1)
    assert not lectura_terminada.wait(0.05)

    completar_tick.set()
    assert lectura_terminada.wait(1)
    hilo_lectura.join()
    ejecutor.detener()

    estado = estados[0]
    assert estado[3] == 60
    assert estado[4] == 95


def test_notifica_estado_despues_del_tick_y_fuera_del_lock() -> None:
    dispositivo = crear_dispositivo()
    selector = crear_selector()
    selector.establecer_fuente_activa(FuenteAmbiente.MANUAL)
    bloqueo_dispositivo = Lock()
    notificacion_recibida = Event()
    estados_publicados: list[tuple[tuple[float, float, Radiacion, Lluvia], float]] = []

    def publicar_estado(
        condiciones: tuple[float, float, Radiacion, Lluvia],
    ) -> None:
        assert bloqueo_dispositivo.acquire(blocking=False)
        bloqueo_dispositivo.release()
        estados_publicados.append((condiciones, dispositivo.humedad_suelo))
        notificacion_recibida.set()

    ejecutor = EjecutorSimulacion(
        dispositivo,
        selector,
        bloqueo_dispositivo,
        publicar_estado,
    )

    ejecutor.iniciar()
    try:
        assert notificacion_recibida.wait(1)
    finally:
        ejecutor.detener()

    assert estados_publicados[0] == (
        (19, 80, Radiacion.BAJA, Lluvia.NINGUNA),
        49.9,
    )
