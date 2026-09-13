from collections.abc import Callable
from threading import Event, Lock, Thread

from ambiente.selector_ambiente import SelectorAmbiente
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import Lluvia, Radiacion
from simulacion.motor_simulacion import MotorSimulacion

INTERVALO_TICK_SEGUNDOS = 1.0
type CondicionesAmbiente = tuple[float, float, Radiacion, Lluvia]


class EjecutorSimulacion:
    def __init__(
        self,
        dispositivo: DispositivoRiego,
        selector_ambiente: SelectorAmbiente,
        bloqueo_dispositivo: Lock,
        al_completar_tick: Callable[[CondicionesAmbiente], None] | None = None,
    ) -> None:
        self._dispositivo = dispositivo
        self._selector_ambiente = selector_ambiente
        self._bloqueo_dispositivo = bloqueo_dispositivo
        self._al_completar_tick = al_completar_tick
        self._evento_detencion = Event()
        self._hilo: Thread | None = None

    @property
    def activo(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    def iniciar(self) -> None:
        if self.activo:
            return

        self._evento_detencion.clear()
        self._hilo = Thread(
            target=self._ejecutar_ciclo,
            name="simulacion-riego",
            daemon=True,
        )
        self._hilo.start()

    def detener(self) -> None:
        self._evento_detencion.set()

        if self._hilo is not None:
            self._hilo.join()
            self._hilo = None

    def _ejecutar_ciclo(self) -> None:
        while not self._evento_detencion.is_set():
            _, condiciones = self._selector_ambiente.obtener_estado_activo()

            with self._bloqueo_dispositivo:
                MotorSimulacion.ejecutar_tick(self._dispositivo, *condiciones)

            if self._al_completar_tick is not None:
                self._al_completar_tick(condiciones)

            self._evento_detencion.wait(INTERVALO_TICK_SEGUNDOS)
