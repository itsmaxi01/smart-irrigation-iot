from threading import Event, Lock, Thread

from ambiente.selector_ambiente import SelectorAmbiente
from dominio.dispositivo_riego import DispositivoRiego
from simulacion.motor_simulacion import MotorSimulacion

INTERVALO_TICK_SEGUNDOS = 1.0


class EjecutorSimulacion:
    def __init__(
        self,
        dispositivo: DispositivoRiego,
        selector_ambiente: SelectorAmbiente,
        bloqueo_dispositivo: Lock,
    ) -> None:
        self._dispositivo = dispositivo
        self._selector_ambiente = selector_ambiente
        self._bloqueo_dispositivo = bloqueo_dispositivo
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
            ambiente = self._selector_ambiente.obtener_ambiente_activo()
            condiciones = ambiente.obtener_condiciones()

            with self._bloqueo_dispositivo:
                MotorSimulacion.ejecutar_tick(self._dispositivo, *condiciones)

            self._evento_detencion.wait(INTERVALO_TICK_SEGUNDOS)
