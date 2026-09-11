from time import sleep as dormir

from ambiente.selector_ambiente import SelectorAmbiente
from dominio.dispositivo_riego import DispositivoRiego
from simulacion.motor_simulacion import MotorSimulacion

INTERVALO_TICK_SEGUNDOS = 1.0


class EjecutorSimulacion:
    def __init__(
        self,
        dispositivo: DispositivoRiego,
        selector_ambiente: SelectorAmbiente,
    ) -> None:
        self._dispositivo = dispositivo
        self._selector_ambiente = selector_ambiente
        self._activo = False

    @property
    def activo(self) -> bool:
        return self._activo

    def ejecutar(self) -> None:
        self._activo = True

        while self._activo:
            ambiente = self._selector_ambiente.obtener_ambiente_activo()
            condiciones = ambiente.obtener_condiciones()
            MotorSimulacion.ejecutar_tick(self._dispositivo, *condiciones)
            dormir(INTERVALO_TICK_SEGUNDOS)

    def detener(self) -> None:
        self._activo = False
