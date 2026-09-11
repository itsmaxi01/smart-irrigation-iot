import pytest

from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import EstadoValvula, Modo, VelocidadRiego


def crear_dispositivo() -> DispositivoRiego:
    return DispositivoRiego(
        modo=Modo.AUTOMATICO,
        velocidad_riego=VelocidadRiego.MEDIA,
        humedad_suelo=40,
        nivel_agua=80,
        humedad_minima=30,
        humedad_objetivo=60,
    )


def test_expone_estado_mediante_propiedades_de_solo_lectura() -> None:
    dispositivo = crear_dispositivo()

    assert dispositivo.modo == Modo.AUTOMATICO
    assert dispositivo.estado_valvula == EstadoValvula.CERRADA
    assert dispositivo.velocidad_riego == VelocidadRiego.MEDIA
    assert dispositivo.humedad_suelo == 40
    assert dispositivo.nivel_agua == 80
    assert dispositivo.humedad_minima == 30
    assert dispositivo.humedad_objetivo == 60


@pytest.mark.parametrize(
    ("atributo", "valor"),
    [
        ("modo", Modo.MANUAL),
        ("estado_valvula", EstadoValvula.ABIERTA),
        ("velocidad_riego", VelocidadRiego.ALTA),
        ("humedad_suelo", 50),
        ("nivel_agua", 50),
        ("humedad_minima", 20),
        ("humedad_objetivo", 70),
    ],
)
def test_impide_cambios_directos_de_estado(atributo: str, valor: object) -> None:
    dispositivo = crear_dispositivo()

    with pytest.raises(AttributeError):
        setattr(dispositivo, atributo, valor)


def test_cambia_estado_mediante_operaciones_de_dominio() -> None:
    dispositivo = crear_dispositivo()

    dispositivo.cambiar_modo(Modo.MANUAL)
    dispositivo.cambiar_velocidad_riego(VelocidadRiego.ALTA)
    dispositivo.abrir_valvula()
    dispositivo.aplicar_cambio_humedad(10)
    agua_consumida = dispositivo.consumir_agua(5)

    assert dispositivo.modo == Modo.MANUAL
    assert dispositivo.velocidad_riego == VelocidadRiego.ALTA
    assert dispositivo.estado_valvula == EstadoValvula.ABIERTA
    assert dispositivo.humedad_suelo == 50
    assert dispositivo.nivel_agua == 75
    assert agua_consumida == 5
