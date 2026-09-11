import pytest

from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import EstadoValvula, Lluvia, Modo, Radiacion, VelocidadRiego
from simulacion.motor_simulacion import (
    MotorSimulacion,
    calcular_aporte_lluvia,
    calcular_aporte_riego,
    calcular_consumo_agua,
    calcular_secado,
)


def crear_dispositivo(
    *,
    modo: Modo = Modo.MANUAL,
    velocidad: VelocidadRiego = VelocidadRiego.MEDIA,
    humedad: float = 50,
    agua: float = 100,
    minima: float = 30,
    objetivo: float = 60,
) -> DispositivoRiego:
    return DispositivoRiego(modo, velocidad, humedad, agua, minima, objetivo)


def ejecutar_tick(
    dispositivo: DispositivoRiego, *, lluvia: Lluvia = Lluvia.NINGUNA
) -> None:
    MotorSimulacion.ejecutar_tick(dispositivo, 19, 80, Radiacion.BAJA, lluvia)


@pytest.mark.parametrize(
    ("temperatura", "humedad_ambiente", "radiacion", "esperado"),
    [
        (19, 71, Radiacion.BAJA, 0.10),
        (20, 70, Radiacion.MEDIA, 0.25),
        (31, 39, Radiacion.ALTA, 0.40),
        (36, 80, Radiacion.BAJA, 0.25),
    ],
)
def test_calcula_secado(
    temperatura: float,
    humedad_ambiente: float,
    radiacion: Radiacion,
    esperado: float,
) -> None:
    assert calcular_secado(temperatura, humedad_ambiente, radiacion) == pytest.approx(esperado)


@pytest.mark.parametrize(
    ("lluvia", "esperado"),
    [
        (Lluvia.NINGUNA, 0.0),
        (Lluvia.LIGERA, 0.30),
        (Lluvia.MODERADA, 0.70),
        (Lluvia.FUERTE, 1.20),
    ],
)
def test_calcula_aporte_lluvia(lluvia: Lluvia, esperado: float) -> None:
    assert calcular_aporte_lluvia(lluvia) == esperado


@pytest.mark.parametrize(
    ("velocidad", "esperado"),
    [
        (VelocidadRiego.BAJA, 0.50),
        (VelocidadRiego.MEDIA, 1.00),
        (VelocidadRiego.ALTA, 1.50),
    ],
)
def test_calcula_aporte_riego(velocidad: VelocidadRiego, esperado: float) -> None:
    assert calcular_aporte_riego(velocidad) == esperado


@pytest.mark.parametrize(
    ("velocidad", "esperado"),
    [
        (VelocidadRiego.BAJA, 0.05),
        (VelocidadRiego.MEDIA, 0.10),
        (VelocidadRiego.ALTA, 0.15),
    ],
)
def test_calcula_consumo_agua(velocidad: VelocidadRiego, esperado: float) -> None:
    assert calcular_consumo_agua(velocidad) == esperado


def test_modo_automatico_abre_bajo_minimo() -> None:
    dispositivo = crear_dispositivo(modo=Modo.AUTOMATICO, humedad=29)

    ejecutar_tick(dispositivo)

    assert dispositivo.estado_valvula == EstadoValvula.ABIERTA


def test_modo_automatico_cierra_en_objetivo() -> None:
    dispositivo = crear_dispositivo(modo=Modo.AUTOMATICO, humedad=60)
    dispositivo.abrir_valvula()

    ejecutar_tick(dispositivo)

    assert dispositivo.estado_valvula == EstadoValvula.CERRADA


@pytest.mark.parametrize("estado_inicial", [EstadoValvula.ABIERTA, EstadoValvula.CERRADA])
def test_modo_automatico_mantiene_valvula_entre_umbrales(
    estado_inicial: EstadoValvula,
) -> None:
    dispositivo = crear_dispositivo(modo=Modo.AUTOMATICO, humedad=45)
    if estado_inicial == EstadoValvula.ABIERTA:
        dispositivo.abrir_valvula()

    ejecutar_tick(dispositivo)

    assert dispositivo.estado_valvula == estado_inicial


@pytest.mark.parametrize("estado_inicial", [EstadoValvula.ABIERTA, EstadoValvula.CERRADA])
def test_modo_manual_no_cambia_valvula_automaticamente(
    estado_inicial: EstadoValvula,
) -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL, humedad=70)
    if estado_inicial == EstadoValvula.ABIERTA:
        dispositivo.abrir_valvula()

    ejecutar_tick(dispositivo)

    assert dispositivo.estado_valvula == estado_inicial


def test_valvula_abierta_aumenta_humedad_y_consume_agua() -> None:
    dispositivo = crear_dispositivo(velocidad=VelocidadRiego.MEDIA)
    dispositivo.abrir_valvula()

    ejecutar_tick(dispositivo)

    assert dispositivo.humedad_suelo == pytest.approx(50.90)
    assert dispositivo.nivel_agua == pytest.approx(99.90)


def test_valvula_cerrada_permite_secado_ambiental() -> None:
    dispositivo = crear_dispositivo(humedad=50)

    ejecutar_tick(dispositivo)

    assert dispositivo.humedad_suelo == pytest.approx(49.90)


def test_lluvia_aumenta_humedad() -> None:
    dispositivo = crear_dispositivo(humedad=50)

    ejecutar_tick(dispositivo, lluvia=Lluvia.MODERADA)

    assert dispositivo.humedad_suelo == pytest.approx(50.60)


def test_tanque_vacio_impide_riego() -> None:
    dispositivo = crear_dispositivo(modo=Modo.AUTOMATICO, humedad=20, agua=0)

    ejecutar_tick(dispositivo)

    assert dispositivo.estado_valvula == EstadoValvula.CERRADA
    assert dispositivo.nivel_agua == 0
    assert dispositivo.humedad_suelo == pytest.approx(19.90)


def test_tanque_que_se_vacia_durante_tick_cierra_valvula() -> None:
    dispositivo = crear_dispositivo(velocidad=VelocidadRiego.ALTA, agua=0.15)
    dispositivo.abrir_valvula()

    ejecutar_tick(dispositivo)

    assert dispositivo.nivel_agua == 0
    assert dispositivo.estado_valvula == EstadoValvula.CERRADA


def test_agua_insuficiente_produce_riego_proporcional() -> None:
    dispositivo = crear_dispositivo(velocidad=VelocidadRiego.ALTA, humedad=50, agua=0.03)
    dispositivo.abrir_valvula()

    ejecutar_tick(dispositivo)

    assert dispositivo.humedad_suelo == pytest.approx(50.20)
    assert dispositivo.nivel_agua == 0
    assert dispositivo.estado_valvula == EstadoValvula.CERRADA


def test_humedad_nunca_supera_cien() -> None:
    dispositivo = crear_dispositivo(humedad=99.9)

    ejecutar_tick(dispositivo, lluvia=Lluvia.FUERTE)

    assert dispositivo.humedad_suelo == 100


def test_humedad_nunca_baja_de_cero() -> None:
    dispositivo = crear_dispositivo(humedad=0)

    ejecutar_tick(dispositivo)

    assert dispositivo.humedad_suelo == 0


@pytest.mark.parametrize(
    ("temperatura", "humedad_ambiente", "radiacion", "lluvia"),
    [
        (float("nan"), 50, Radiacion.BAJA, Lluvia.NINGUNA),
        (-274, 50, Radiacion.BAJA, Lluvia.NINGUNA),
        (25, -1, Radiacion.BAJA, Lluvia.NINGUNA),
        (25, 101, Radiacion.BAJA, Lluvia.NINGUNA),
        (25, 50, "baja", Lluvia.NINGUNA),
        (25, 50, Radiacion.BAJA, "ninguna"),
    ],
)
def test_tick_rechaza_valores_ambientales_imposibles(
    temperatura: float,
    humedad_ambiente: float,
    radiacion: object,
    lluvia: object,
) -> None:
    dispositivo = crear_dispositivo()

    with pytest.raises(ValueError):
        MotorSimulacion.ejecutar_tick(  # type: ignore[arg-type]
            dispositivo, temperatura, humedad_ambiente, radiacion, lluvia
        )
