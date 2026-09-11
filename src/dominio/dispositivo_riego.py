# pyright: reportUnnecessaryIsInstance=false

from dominio.enumeraciones import EstadoValvula, Modo, VelocidadRiego


class DispositivoRiego:
    def __init__(
        self,
        modo: Modo,
        velocidad_riego: VelocidadRiego,
        humedad_suelo: float,
        nivel_agua: float,
        humedad_minima: float,
        humedad_objetivo: float,
    ) -> None:
        self._modo = modo
        self._velocidad_riego = velocidad_riego
        self._humedad_suelo = humedad_suelo
        self._nivel_agua = nivel_agua
        self._humedad_minima = humedad_minima
        self._humedad_objetivo = humedad_objetivo
        self._estado_valvula = EstadoValvula.CERRADA

        self._validar_estado_inicial()

    @property
    def modo(self) -> Modo:
        return self._modo

    @property
    def estado_valvula(self) -> EstadoValvula:
        return self._estado_valvula

    @property
    def velocidad_riego(self) -> VelocidadRiego:
        return self._velocidad_riego

    @property
    def humedad_suelo(self) -> float:
        return self._humedad_suelo

    @property
    def nivel_agua(self) -> float:
        return self._nivel_agua

    @property
    def humedad_minima(self) -> float:
        return self._humedad_minima

    @property
    def humedad_objetivo(self) -> float:
        return self._humedad_objetivo

    def _validar_estado_inicial(self) -> None:
        if not isinstance(self._modo, Modo):
            raise ValueError("El modo del dispositivo no es válido")

        if not isinstance(self._velocidad_riego, VelocidadRiego):
            raise ValueError("La velocidad de riego no es válida")

        if not 0 <= self._humedad_suelo <= 100:
            raise ValueError("La humedad del suelo debe estar entre 0 y 100")

        if not 0 <= self._nivel_agua <= 100:
            raise ValueError("El nivel de agua debe estar entre 0 y 100")

        if not 0 <= self._humedad_minima <= 100:
            raise ValueError("La humedad mínima debe estar entre 0 y 100")

        if not 0 <= self._humedad_objetivo <= 100:
            raise ValueError("La humedad objetivo debe estar entre 0 y 100")

        if self._humedad_minima >= self._humedad_objetivo:
            raise ValueError("La humedad mínima debe ser menor que la humedad objetivo")

    def abrir_valvula(self) -> None:
        if self._nivel_agua <= 0:
            raise ValueError("El nivel de agua debe ser mayor a 0 para abrir la válvula")

        self._estado_valvula = EstadoValvula.ABIERTA

    def cerrar_valvula(self) -> None:
        self._estado_valvula = EstadoValvula.CERRADA

    def cambiar_modo(self, modo: Modo) -> None:
        if not isinstance(modo, Modo):
            raise ValueError("El modo del dispositivo no es válido")

        self._modo = modo

    def cambiar_velocidad_riego(self, velocidad_riego: VelocidadRiego) -> None:
        if not isinstance(velocidad_riego, VelocidadRiego):
            raise ValueError("La velocidad de riego no es válida")

        self._velocidad_riego = velocidad_riego

    def aplicar_cambio_humedad(self, delta: float) -> None:
        nueva_humedad = self._humedad_suelo + delta
        self._humedad_suelo = max(0, min(100, nueva_humedad))

    def consumir_agua(self, cantidad: float) -> float:
        if cantidad < 0:
            raise ValueError("La cantidad de agua a consumir no puede ser negativa")

        agua_consumida = min(self._nivel_agua, cantidad)

        self._nivel_agua -= agua_consumida

        if self._nivel_agua <= 0:
            self._nivel_agua = 0
            self.cerrar_valvula()

        return agua_consumida
