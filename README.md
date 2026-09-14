# Smart Irrigation IoT Simulator

Simulador local de un dispositivo de riego inteligente. Mantiene un estado físico en
memoria, ejecuta un ciclo de simulación periódico y puede operarse desde una interfaz
web, una API REST o Home Assistant mediante MQTT.

El modelo busca demostrar integración IoT y reglas de negocio observables; no pretende
ser un modelo agronómico de precisión.

## Funcionalidad

- Modos `AUTOMATICO` y `MANUAL`, con control manual de la válvula solo en `MANUAL`.
- Simulación de humedad del suelo y consumo del tanque cada segundo.
- Condiciones ambientales aleatorias fijas por ejecución o configurables manualmente.
- API REST documentada con OpenAPI y contrato uniforme de errores.
- Cliente MQTT bidireccional con Discovery, availability, LWT y resincronización.
- Interfaz web responsive servida por FastAPI, sin dependencias frontend externas.
- Stack local con FastAPI, Mosquitto y Home Assistant mediante Docker Compose.

## Arquitectura

`DispositivoRiego` mantiene el estado autoritativo y protege las invariantes físicas.
Las rutas del dispositivo y el cliente MQTT reutilizan `ServicioDispositivo`; el ciclo
de simulación opera sobre la misma instancia y comparte su lock.

La API también configura `SelectorAmbiente`. En cada ciclo, `EjecutorSimulacion` obtiene
del selector las condiciones vigentes y delega el tick físico a `MotorSimulacion`.

La descripción de componentes, flujos, concurrencia y contratos MQTT está en
[ARCHITECTURE.md](ARCHITECTURE.md).

## Inicio rápido con Docker

Requisito: Docker Desktop con Docker Compose.

```console
docker compose up --build
```

Servicios disponibles:

- Aplicación y frontend: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- Home Assistant: <http://localhost:8123>

### Configurar Home Assistant

Home Assistant conserva su configuración, pero no incluye usuarios ni credenciales en
Git. En el primer arranque:

1. Completa el onboarding en <http://localhost:8123>.
2. Abre **Settings > Devices & services > Add integration > MQTT**.
3. Usa `mosquitto` como broker y `1883` como puerto, sin usuario ni contraseña.
4. Espera a que MQTT Discovery registre el dispositivo **Smart Irrigation**.

Discovery crea tres controles y ocho sensores. El dashboard creado desde la interfaz de
Home Assistant se guarda en el volumen local, pero no está versionado; una instalación
nueva recibe las entidades, no un dashboard personalizado.

Para detener los contenedores sin perder la configuración:

```console
docker compose down
```

## API REST

| Método | Ruta | Propósito |
|---|---|---|
| `GET` | `/api/device` | Consultar el estado del dispositivo |
| `PATCH` | `/api/device/mode` | Cambiar modo |
| `PATCH` | `/api/device/speed` | Cambiar velocidad |
| `PATCH` | `/api/device/valve` | Operar la válvula en modo manual |
| `GET` | `/api/environment` | Consultar la fuente y condiciones activas |
| `GET` | `/api/environment/source` | Consultar la fuente activa |
| `PATCH` | `/api/environment/source` | Seleccionar `ALEATORIO` o `MANUAL` |
| `GET` | `/api/environment/manual` | Consultar el perfil manual guardado |
| `PUT` | `/api/environment/manual` | Reemplazar el perfil manual completo |

Los payloads usan nombres en inglés y valores enum en mayúsculas. Swagger contiene los
esquemas y respuestas de error disponibles.

## MQTT

Dentro de Compose, tanto Home Assistant como el simulador usan `mosquitto:1883`. Para
ejecución local del simulador, el valor predeterminado es `localhost:1883`.

El dispositivo publica un snapshot completo en `smart-irrigation/device/state` y recibe
comandos en:

- `smart-irrigation/device/mode/set`
- `smart-irrigation/device/speed/set`
- `smart-irrigation/device/valve/set`

Los topics, payloads, QoS y comportamiento de reconexión están documentados en
[ARCHITECTURE.md](ARCHITECTURE.md#mqtt-y-home-assistant).

## Desarrollo local

Requiere Python 3.13.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn api.principal:app --app-dir src --reload
```

El cliente MQTT intenta conectarse en segundo plano. Para probar MQTT fuera de Docker se
necesita un broker accesible en `localhost:1883` o definir `MQTT_HOST` y `MQTT_PORT`.

## Verificación

```console
pytest
ruff check .
pyright
```

Los tests cubren dominio, simulación, selección ambiental, contratos REST, errores HTTP,
mapeo MQTT, lifecycle del cliente y coordinación concurrente. El repositorio no publica
una métrica de cobertura.

## Estructura

```text
src/
├── dominio/       Estado e invariantes del dispositivo
├── aplicacion/    Casos de uso compartidos por REST y MQTT
├── ambiente/      Fuentes manual y aleatoria
├── simulacion/    Cálculo y ejecución periódica
├── mqtt/          Cliente, topics, mapeo y Discovery
└── api/           FastAPI, contratos y errores HTTP
frontend/          HTML, CSS y JavaScript vanilla
tests/             Tests automatizados
docker/mosquitto/  Configuración local del broker
```

## Decisiones y límites

- Un proceso representa un único dispositivo; Uvicorn usa un worker.
- El estado del dispositivo vive en memoria y vuelve a sus valores iniciales al reiniciar.
- Mosquitto permite conexiones anónimas únicamente para la demo local.
- Los volúmenes conservan retained messages y configuración de Home Assistant.
- No hay autenticación, TLS, ACL, historial de telemetría ni soporte multi-dispositivo.
- Compose no incluye healthchecks: el cliente MQTT tolera que el broker arranque después.
