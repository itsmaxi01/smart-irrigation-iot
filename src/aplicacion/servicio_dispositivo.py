from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import Modo, VelocidadRiego


class ServicioDispositivo:
    def __init__(self, dispositivo: DispositivoRiego) -> None:
        self._dispositivo = dispositivo

    @property
    def dispositivo(self) -> DispositivoRiego:
        return self._dispositivo

    def cambiar_modo(self, modo: Modo) -> None:
        self._dispositivo.cambiar_modo(modo)

    def cambiar_velocidad_riego(self, velocidad: VelocidadRiego) -> None:
        self._dispositivo.cambiar_velocidad_riego(velocidad)

    def abrir_valvula(self) -> None:
        self._validar_control_manual_valvula()
        self._dispositivo.abrir_valvula()

    def cerrar_valvula(self) -> None:
        self._validar_control_manual_valvula()
        self._dispositivo.cerrar_valvula()

    def _validar_control_manual_valvula(self) -> None:
        if self._dispositivo.modo != Modo.MANUAL:
            raise ValueError("La válvula solo puede controlarse en modo manual")
