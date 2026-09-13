# pyright: reportUnnecessaryIsInstance=false

from threading import Lock

from ambiente.ambiente_aleatorio import AmbienteAleatorio
from ambiente.ambiente_manual import AmbienteManual
from dominio.enumeraciones import FuenteAmbiente, Lluvia, Radiacion

type CondicionesAmbiente = tuple[float, float, Radiacion, Lluvia]


class SelectorAmbiente:
    def __init__(
        self,
        ambiente_manual: AmbienteManual,
        ambiente_aleatorio: AmbienteAleatorio,
    ) -> None:
        self._ambiente_manual = ambiente_manual
        self._ambiente_aleatorio = ambiente_aleatorio
        self._fuente_activa = FuenteAmbiente.ALEATORIO
        self._bloqueo = Lock()

    @property
    def fuente_activa(self) -> FuenteAmbiente:
        with self._bloqueo:
            return self._fuente_activa

    def establecer_fuente_activa(self, fuente: FuenteAmbiente) -> None:
        if not isinstance(fuente, FuenteAmbiente):
            raise ValueError("Fuente de ambiente no válida")

        with self._bloqueo:
            self._fuente_activa = fuente

    def obtener_ambiente_activo(self) -> AmbienteManual | AmbienteAleatorio:
        with self._bloqueo:
            return self._obtener_ambiente_activo()

    def obtener_estado_activo(self) -> tuple[FuenteAmbiente, CondicionesAmbiente]:
        with self._bloqueo:
            fuente = self._fuente_activa
            condiciones = self._obtener_ambiente_activo().obtener_condiciones()
            return fuente, condiciones

    def obtener_condiciones_manuales(self) -> CondicionesAmbiente:
        with self._bloqueo:
            return self._ambiente_manual.obtener_condiciones()

    def actualizar_ambiente_manual(
        self,
        temperatura: float,
        humedad_ambiente: float,
        radiacion: Radiacion,
        lluvia: Lluvia,
    ) -> None:
        with self._bloqueo:
            if self._fuente_activa != FuenteAmbiente.MANUAL:
                raise ValueError(
                    "El ambiente manual solo puede modificarse cuando la fuente es MANUAL"
                )

            self._ambiente_manual.actualizar_condiciones(
                temperatura,
                humedad_ambiente,
                radiacion,
                lluvia,
            )

    def _obtener_ambiente_activo(self) -> AmbienteManual | AmbienteAleatorio:
        if self._fuente_activa == FuenteAmbiente.MANUAL:
            return self._ambiente_manual

        if self._fuente_activa == FuenteAmbiente.ALEATORIO:
            return self._ambiente_aleatorio

        raise ValueError("Fuente de ambiente no válida")
