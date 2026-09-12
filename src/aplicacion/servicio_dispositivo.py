from threading import Lock

from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import EstadoValvula, Modo, VelocidadRiego


class ServicioDispositivo:
    def __init__(self, dispositivo: DispositivoRiego, bloqueo_dispositivo: Lock) -> None:
        self._dispositivo = dispositivo
        self._bloqueo_dispositivo = bloqueo_dispositivo

    def obtener_estado(
        self,
    ) -> tuple[Modo, EstadoValvula, VelocidadRiego, float, float, float, float]:
        with self._bloqueo_dispositivo:
            return (
                self._dispositivo.modo,
                self._dispositivo.estado_valvula,
                self._dispositivo.velocidad_riego,
                self._dispositivo.humedad_suelo,
                self._dispositivo.nivel_agua,
                self._dispositivo.humedad_minima,
                self._dispositivo.humedad_objetivo,
            )

    def cambiar_modo(self, modo: Modo) -> None:
        with self._bloqueo_dispositivo:
            self._dispositivo.cambiar_modo(modo)

    def cambiar_velocidad_riego(self, velocidad: VelocidadRiego) -> None:
        with self._bloqueo_dispositivo:
            self._dispositivo.cambiar_velocidad_riego(velocidad)

    def abrir_valvula(self) -> None:
        with self._bloqueo_dispositivo:
            self._validar_control_manual_valvula()
            self._dispositivo.abrir_valvula()

    def cerrar_valvula(self) -> None:
        with self._bloqueo_dispositivo:
            self._validar_control_manual_valvula()
            self._dispositivo.cerrar_valvula()

    def _validar_control_manual_valvula(self) -> None:
        if self._dispositivo.modo != Modo.MANUAL:
            raise ValueError("La válvula solo puede controlarse en modo manual")
