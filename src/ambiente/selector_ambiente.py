# pyright: reportUnnecessaryIsInstance=false

from ambiente.ambiente_aleatorio import AmbienteAleatorio
from ambiente.ambiente_manual import AmbienteManual
from dominio.enumeraciones import FuenteAmbiente


class SelectorAmbiente:
    def __init__(
        self,
        ambiente_manual: AmbienteManual,
        ambiente_aleatorio: AmbienteAleatorio,
    ) -> None:
        self._ambiente_manual = ambiente_manual
        self._ambiente_aleatorio = ambiente_aleatorio
        self._fuente_activa = FuenteAmbiente.ALEATORIO

    @property
    def fuente_activa(self) -> FuenteAmbiente:
        return self._fuente_activa

    def establecer_fuente_activa(self, fuente: FuenteAmbiente) -> None:
        if not isinstance(fuente, FuenteAmbiente):
            raise ValueError("Fuente de ambiente no válida")

        self._fuente_activa = fuente

    def obtener_ambiente_activo(self) -> AmbienteManual | AmbienteAleatorio:
        if self._fuente_activa == FuenteAmbiente.MANUAL:
            return self._ambiente_manual

        if self._fuente_activa == FuenteAmbiente.ALEATORIO:
            return self._ambiente_aleatorio

        raise ValueError("Fuente de ambiente no válida")
