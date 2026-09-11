import pytest

from aplicacion.servicio_dispositivo import ServicioDispositivo
from dominio.dispositivo_riego import DispositivoRiego
from dominio.enumeraciones import EstadoValvula, Modo, VelocidadRiego


def crear_dispositivo(
    *,
    modo: Modo = Modo.MANUAL,
    velocidad_riego: VelocidadRiego = VelocidadRiego.MEDIA,
    humedad_suelo: float = 40,
    nivel_agua: float = 80,
) -> DispositivoRiego:
    return DispositivoRiego(
        modo=modo,
        velocidad_riego=velocidad_riego,
        humedad_suelo=humedad_suelo,
        nivel_agua=nivel_agua,
        humedad_minima=30,
        humedad_objetivo=60,
    )


def test_cambia_de_manual_a_automatico() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL)
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_modo(Modo.AUTOMATICO)

    assert dispositivo.modo == Modo.AUTOMATICO


def test_cambia_de_automatico_a_manual() -> None:
    dispositivo = crear_dispositivo(modo=Modo.AUTOMATICO)
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_modo(Modo.MANUAL)

    assert dispositivo.modo == Modo.MANUAL


@pytest.mark.parametrize("modo", [Modo.MANUAL, Modo.AUTOMATICO])
def test_cambia_velocidad_en_cualquier_modo(modo: Modo) -> None:
    dispositivo = crear_dispositivo(modo=modo, velocidad_riego=VelocidadRiego.BAJA)
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_velocidad_riego(velocidad=VelocidadRiego.ALTA)

    assert dispositivo.velocidad_riego == VelocidadRiego.ALTA


def test_abre_valvula_en_manual_con_agua() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL, nivel_agua=10)
    servicio = ServicioDispositivo(dispositivo)

    servicio.abrir_valvula()

    assert dispositivo.estado_valvula == EstadoValvula.ABIERTA


def test_cierra_valvula_en_manual() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL)
    servicio = ServicioDispositivo(dispositivo)
    servicio.abrir_valvula()

    servicio.cerrar_valvula()

    assert dispositivo.estado_valvula == EstadoValvula.CERRADA


def test_rechaza_abrir_valvula_en_automatico() -> None:
    dispositivo = crear_dispositivo(modo=Modo.AUTOMATICO)
    servicio = ServicioDispositivo(dispositivo)

    with pytest.raises(ValueError, match="solo puede controlarse en modo manual"):
        servicio.abrir_valvula()

    assert dispositivo.estado_valvula == EstadoValvula.CERRADA


def test_rechaza_cerrar_valvula_en_automatico() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL)
    servicio = ServicioDispositivo(dispositivo)
    servicio.abrir_valvula()
    dispositivo.cambiar_modo(Modo.AUTOMATICO)

    with pytest.raises(ValueError, match="solo puede controlarse en modo manual"):
        servicio.cerrar_valvula()

    assert dispositivo.estado_valvula == EstadoValvula.ABIERTA


def test_cambiar_velocidad_no_modifica_humedad_suelo() -> None:
    dispositivo = crear_dispositivo(humedad_suelo=45)
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_velocidad_riego(VelocidadRiego.ALTA)

    assert dispositivo.humedad_suelo == 45


def test_cambiar_velocidad_no_modifica_nivel_agua() -> None:
    dispositivo = crear_dispositivo(nivel_agua=75)
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_velocidad_riego(VelocidadRiego.ALTA)

    assert dispositivo.nivel_agua == 75


def test_cambiar_modo_no_modifica_estado_fisico() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL, humedad_suelo=45, nivel_agua=75)
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_modo(Modo.AUTOMATICO)

    assert dispositivo.humedad_suelo == 45
    assert dispositivo.nivel_agua == 75


def test_servicio_modifica_la_misma_instancia_recibida() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL)
    servicio = ServicioDispositivo(dispositivo)

    servicio.abrir_valvula()

    assert dispositivo.estado_valvula == EstadoValvula.ABIERTA


def test_delega_validacion_fisica_de_agua_al_dispositivo() -> None:
    dispositivo = crear_dispositivo(modo=Modo.MANUAL, nivel_agua=0)
    servicio = ServicioDispositivo(dispositivo)

    with pytest.raises(ValueError, match="nivel de agua"):
        servicio.abrir_valvula()


@pytest.mark.parametrize(
    ("modo_inicial", "modo_final"),
    [(Modo.MANUAL, Modo.AUTOMATICO), (Modo.AUTOMATICO, Modo.MANUAL)],
)
@pytest.mark.parametrize("valvula_abierta", [False, True])
def test_cambiar_modo_conserva_valvula_y_estado_fisico(
    modo_inicial: Modo, modo_final: Modo, valvula_abierta: bool
) -> None:
    dispositivo = crear_dispositivo(modo=modo_inicial, humedad_suelo=20)
    if valvula_abierta:
        dispositivo.abrir_valvula()
    estado_inicial = dispositivo.estado_valvula
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_modo(modo_final)

    assert dispositivo.modo == modo_final
    assert dispositivo.estado_valvula == estado_inicial
    assert dispositivo.humedad_suelo == 20
    assert dispositivo.nivel_agua == 80


@pytest.mark.parametrize("modo", [Modo.MANUAL, Modo.AUTOMATICO])
def test_cambiar_velocidad_con_valvula_abierta_no_produce_riego(modo: Modo) -> None:
    dispositivo = crear_dispositivo(modo=modo)
    dispositivo.abrir_valvula()
    servicio = ServicioDispositivo(dispositivo)

    servicio.cambiar_velocidad_riego(velocidad=VelocidadRiego.ALTA)

    assert dispositivo.velocidad_riego == VelocidadRiego.ALTA
    assert dispositivo.estado_valvula == EstadoValvula.ABIERTA
    assert dispositivo.humedad_suelo == 40
    assert dispositivo.nivel_agua == 80
