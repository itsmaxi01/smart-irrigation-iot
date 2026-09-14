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

Requisito: Git y Docker Desktop con Docker Compose.

```powershell
git clone https://github.com/itsmaxi01/smart-irrigation-iot.git
cd smart-irrigation-iot
docker compose pull
docker compose up --build -d
docker compose ps
```

La primera construcción puede tardar varios minutos. Cuando los tres servicios aparezcan
en ejecución, abre:

- Aplicación y frontend: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- Home Assistant: <http://localhost:8123>

### Configurar Home Assistant

Home Assistant conserva usuarios, credenciales e integraciones en un volumen local, pero
ninguno de esos datos sensibles se incluye en Git. El repositorio sí distribuye un
dashboard **Smart Irrigation** reproducible. En el primer arranque:

1. Entra a <http://localhost:8123> y crea tu propio usuario durante el onboarding.
2. Completa nombre del hogar, ubicación, zona horaria y preferencias de privacidad.
3. Abre **Settings > Devices & services**.
4. Pulsa **Add integration**, busca **MQTT** y selecciónala.
5. Escribe `mosquitto` en **Broker** y `1883` en **Port**. Deja vacíos usuario y
   contraseña.
6. Finaliza la integración y espera unos segundos a que MQTT Discovery registre el
   dispositivo **Smart Irrigation**.
7. Abre **Smart Irrigation** desde la barra lateral. También puedes entrar directamente
   en <http://localhost:8123/irrigation-dashboard/irrigation>. El dashboard mostrará los
   sensores y permitirá operar modo, velocidad y válvula.

Discovery crea tres controles y ocho sensores. La válvula solo acepta cambios cuando el
dispositivo está en modo `MANUAL`; en `AUTOMATICO`, la política del simulador conserva el
control.

Si Home Assistant todavía está iniciando, revisa su progreso con:

```powershell
docker compose logs -f home-assistant
```

Presiona `Ctrl+C` para salir de los logs sin detener los contenedores.

Para detener los contenedores sin perder la configuración:

```console
docker compose down
```

Para volver a iniciar conservando onboarding y configuración:

```powershell
docker compose up -d
```

Para eliminar también todos los datos locales y repetir el onboarding desde cero:

```powershell
docker compose down -v
```

Este último comando elimina los volúmenes de Mosquitto y Home Assistant.

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
docker/homeassistant/ Configuración y dashboard Lovelace reproducibles
```

## Decisiones y límites

- Un proceso representa un único dispositivo; Uvicorn usa un worker.
- El estado del dispositivo vive en memoria y vuelve a sus valores iniciales al reiniciar.
- Mosquitto permite conexiones anónimas únicamente para la demo local.
- Los volúmenes conservan retained messages y configuración de Home Assistant.
- No hay autenticación, TLS, ACL, historial de telemetría ni soporte multi-dispositivo.
- Compose no incluye healthchecks: el cliente MQTT tolera que el broker arranque después.
