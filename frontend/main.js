"use strict";

const POLLING_INTERVAL_MS = 1500;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 88;

const MODE_LABELS = {
  AUTOMATICO: "Automatic",
  MANUAL: "Manual",
};

const ENUM_LABELS = {
  BAJA: "Low",
  MEDIA: "Medium",
  ALTA: "High",
  NINGUNA: "None",
  LIGERA: "Light",
  MODERADA: "Moderate",
  FUERTE: "Heavy",
  ALEATORIO: "Random",
  MANUAL: "Manual",
};

// 1. API

class ApiError extends Error {
  constructor(response, payload) {
    super(payload?.message || `Request failed with status ${response.status}`);
    this.name = "ApiError";
    this.status = response.status;
    this.code = payload?.code || "HTTP_ERROR";
    this.fields = Array.isArray(payload?.fields) ? payload.fields : [];
  }
}

async function solicitarJson(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: options.body
      ? { "Content-Type": "application/json", ...options.headers }
      : options.headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    throw new ApiError(response, payload);
  }

  return payload;
}

function obtenerDispositivo() {
  return solicitarJson("/api/device");
}

function cambiarModo(mode) {
  return solicitarJson("/api/device/mode", {
    method: "PATCH",
    body: JSON.stringify({ mode }),
  });
}

function cambiarVelocidad(speed) {
  return solicitarJson("/api/device/speed", {
    method: "PATCH",
    body: JSON.stringify({ speed }),
  });
}

function cambiarValvula(state) {
  return solicitarJson("/api/device/valve", {
    method: "PATCH",
    body: JSON.stringify({ state }),
  });
}

function obtenerAmbiente() {
  return solicitarJson("/api/environment");
}

function obtenerAmbienteManual() {
  return solicitarJson("/api/environment/manual");
}

function cambiarFuenteAmbiente(source) {
  return solicitarJson("/api/environment/source", {
    method: "PATCH",
    body: JSON.stringify({ source }),
  });
}

function actualizarAmbienteManual(conditions) {
  return solicitarJson("/api/environment/manual", {
    method: "PUT",
    body: JSON.stringify(conditions),
  });
}

// 2. DOM helpers and references

const dom = {
  connectionStatus: document.querySelector("#connection-status"),
  connectionLabel: document.querySelector("#connection-label"),
  modeBadge: document.querySelector("#mode-badge"),
  soilMoisture: document.querySelector("#soil-moisture"),
  minimumMoisture: document.querySelector("#minimum-moisture"),
  targetMoisture: document.querySelector("#target-moisture"),
  moistureGauge: document.querySelector("#moisture-gauge"),
  moistureProgress: document.querySelector("#moisture-progress"),
  moistureAssessment: document.querySelector("#moisture-assessment"),
  valveBadge: document.querySelector("#valve-badge"),
  gardenVisual: document.querySelector("#garden-visual"),
  waterLevel: document.querySelector("#water-level"),
  waterProgress: document.querySelector("#water-progress"),
  waterProgressFill: document.querySelector("#water-progress-fill"),
  environmentSourceBadge: document.querySelector("#environment-source-badge"),
  temperature: document.querySelector("#temperature"),
  ambientHumidity: document.querySelector("#ambient-humidity"),
  radiation: document.querySelector("#radiation"),
  rain: document.querySelector("#rain"),
  modeControls: document.querySelector("#mode-controls"),
  speedControls: document.querySelector("#speed-controls"),
  valveControls: document.querySelector("#valve-controls"),
  valveHint: document.querySelector("#valve-hint"),
  sourceControls: document.querySelector("#source-controls"),
  manualForm: document.querySelector("#manual-environment-form"),
  manualFields: document.querySelector("#manual-environment-fields"),
  conditionsEditorTitle: document.querySelector("#conditions-editor-title"),
  manualDisabledNote: document.querySelector("#manual-disabled-note"),
  manualTemperature: document.querySelector("#manual-temperature"),
  manualHumidity: document.querySelector("#manual-humidity"),
  manualRadiation: document.querySelector("#manual-radiation"),
  manualRain: document.querySelector("#manual-rain"),
  feedback: document.querySelector("#feedback"),
  feedbackMessage: document.querySelector("#feedback-message"),
};

function limitarPorcentaje(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.min(100, Math.max(0, number)) : 0;
}

function formatearNumero(value, maximumFractionDigits = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US", { maximumFractionDigits }).format(number);
}

function marcarSeleccion(container, attribute, selectedValue) {
  container.querySelectorAll(`button[${attribute}]`).forEach((button) => {
    const selected = button.getAttribute(attribute) === selectedValue;
    button.classList.toggle("is-active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

function estaOcupado(container) {
  return container.dataset.busy === "true";
}

function establecerOcupado(container, busy) {
  container.dataset.busy = String(busy);
  container.querySelectorAll("button").forEach((button) => {
    button.disabled = busy;
  });
}

function actualizarCampoSiNoEditando(field, value) {
  if (document.activeElement !== field) {
    field.value = value;
  }
}

function limpiarErroresCampos() {
  dom.manualForm.querySelectorAll("[aria-invalid='true']").forEach((field) => {
    field.removeAttribute("aria-invalid");
  });
}

// 3. Render

function renderDispositivo(device) {
  const moisture = limitarPorcentaje(device.soil_moisture);
  const waterLevel = limitarPorcentaje(device.water_level);
  const minimum = Number(device.minimum_moisture);
  const target = Number(device.target_moisture);

  dom.soilMoisture.textContent = formatearNumero(device.soil_moisture);
  dom.minimumMoisture.textContent = formatearNumero(minimum);
  dom.targetMoisture.textContent = formatearNumero(target);
  dom.modeBadge.textContent = MODE_LABELS[device.mode] || device.mode;
  dom.moistureGauge.setAttribute("aria-valuenow", String(moisture));
  dom.moistureProgress.style.strokeDashoffset = String(
    GAUGE_CIRCUMFERENCE * (1 - moisture / 100),
  );

  if (moisture < minimum) {
    dom.moistureAssessment.textContent = "Below minimum";
  } else if (moisture >= target) {
    dom.moistureAssessment.textContent = "Target reached";
  } else {
    dom.moistureAssessment.textContent = "Within irrigation range";
  }

  const valveOpen = device.valve === "ABIERTA";
  dom.valveBadge.textContent = valveOpen ? "Valve Open" : "Valve Closed";
  dom.valveBadge.classList.toggle("is-open", valveOpen);
  dom.gardenVisual.classList.toggle("valve-open", valveOpen);

  dom.waterLevel.textContent = formatearNumero(device.water_level);
  dom.waterProgress.setAttribute("aria-valuenow", String(waterLevel));
  dom.waterProgressFill.style.width = `${waterLevel}%`;
  dom.waterProgress.classList.toggle("is-low", waterLevel < 20);

  renderControles(device);
}

function renderAmbiente(environment) {
  dom.environmentSourceBadge.textContent = `Source · ${ENUM_LABELS[environment.source] || environment.source}`;
  dom.temperature.textContent = formatearNumero(environment.temperature);
  dom.ambientHumidity.textContent = formatearNumero(environment.ambient_humidity);
  dom.radiation.textContent = ENUM_LABELS[environment.radiation] || environment.radiation;
  dom.rain.textContent = ENUM_LABELS[environment.rain] || environment.rain;
  renderFuenteAmbiente(environment.source);
}

function renderAmbienteManual(environment) {
  if (dom.manualForm.dataset.dirty === "true") {
    return;
  }

  actualizarCampoSiNoEditando(dom.manualTemperature, environment.temperature);
  actualizarCampoSiNoEditando(dom.manualHumidity, environment.ambient_humidity);
  actualizarCampoSiNoEditando(dom.manualRadiation, environment.radiation);
  actualizarCampoSiNoEditando(dom.manualRain, environment.rain);
}

function renderControles(device) {
  marcarSeleccion(dom.modeControls, "data-mode", device.mode);
  marcarSeleccion(dom.speedControls, "data-speed", device.irrigation_speed);
  marcarSeleccion(dom.valveControls, "data-valve", device.valve);

  const automatic = device.mode === "AUTOMATICO";
  const valveBusy = estaOcupado(dom.valveControls);
  dom.modeControls.querySelectorAll("button").forEach((button) => {
    button.disabled = estaOcupado(dom.modeControls);
  });
  dom.speedControls.querySelectorAll("button").forEach((button) => {
    button.disabled = estaOcupado(dom.speedControls);
  });
  dom.valveControls.querySelectorAll("button").forEach((button) => {
    button.disabled = automatic || valveBusy;
  });

  dom.valveHint.textContent = automatic
    ? "Valve is controlled automatically in Automatic mode."
    : "Manual valve control is available.";
  dom.valveHint.classList.toggle("is-manual", !automatic);
}

function renderFuenteAmbiente(source) {
  marcarSeleccion(dom.sourceControls, "data-source", source);
  const sourceBusy = estaOcupado(dom.sourceControls);
  dom.sourceControls.querySelectorAll("button").forEach((button) => {
    button.disabled = sourceBusy;
  });

  const manual = source === "MANUAL";
  const formBusy = dom.manualFields.dataset.busy === "true";
  dom.manualFields.disabled = !manual || formBusy;
  dom.conditionsEditorTitle.textContent = manual
    ? "Manual conditions"
    : "Live random conditions";
  dom.manualDisabledNote.textContent = manual
    ? ""
    : "Current simulated conditions are read-only. Switch the source to Manual to edit them.";
}

function renderEstadoConexion(connected) {
  const state = connected ? "connected" : "disconnected";
  dom.connectionStatus.dataset.state = state;
  dom.connectionStatus.classList.toggle("is-connected", connected);
  dom.connectionStatus.classList.toggle("is-disconnected", !connected);
  dom.connectionStatus.classList.remove("is-connecting");
  dom.connectionLabel.textContent = connected ? "Connected" : "Disconnected";
}

// 4. User feedback

let feedbackTimerId = null;

function mostrarFeedback(message, type = "success", duration = 3200) {
  if (feedbackTimerId !== null) {
    window.clearTimeout(feedbackTimerId);
  }

  dom.feedbackMessage.textContent = message;
  dom.feedback.classList.toggle("is-error", type === "error");
  dom.feedback.classList.toggle("is-warning", type === "warning");
  dom.feedback.hidden = false;

  feedbackTimerId = window.setTimeout(() => {
    dom.feedback.hidden = true;
    feedbackTimerId = null;
  }, duration);
}

function mensajeParaError(error) {
  if (!(error instanceof ApiError)) {
    return "The simulator could not be reached. The dashboard will keep trying.";
  }

  if (error.code === "VALIDATION_ERROR" && error.fields.length > 0) {
    return error.fields.map((field) => `${field.field}: ${field.message}`).join(" · ");
  }

  const messagesByCode = {
    MANUAL_ENVIRONMENT_REQUIRED:
      "Switch the environment source to Manual before editing conditions.",
    VALVE_CONTROL_REQUIRES_MANUAL_MODE:
      "Switch the device to Manual mode before operating the valve.",
    RESOURCE_NOT_FOUND: "The requested simulator resource was not found.",
    METHOD_NOT_ALLOWED: "This action is not supported by the simulator API.",
    INTERNAL_ERROR: "The simulator could not complete the action.",
  };

  return messagesByCode[error.code] || error.message;
}

function marcarCamposInvalidos(error) {
  limpiarErroresCampos();
  if (!(error instanceof ApiError) || error.code !== "VALIDATION_ERROR") {
    return;
  }

  error.fields.forEach(({ field }) => {
    const input = dom.manualForm.elements.namedItem(field);
    if (input instanceof HTMLElement) {
      input.setAttribute("aria-invalid", "true");
    }
  });
}

async function ejecutarComando(container, command, successMessage, renderResponse) {
  establecerOcupado(container, true);
  try {
    const response = await command();
    if (renderResponse) {
      renderResponse(response);
    }
    mostrarFeedback(successMessage);
  } catch (error) {
    mostrarFeedback(mensajeParaError(error), "error", 5000);
  } finally {
    establecerOcupado(container, false);
    await actualizarVista();
  }
}

// 5. Event handlers

function registrarEventos() {
  dom.modeControls.querySelectorAll("button[data-mode]").forEach((button) => {
    button.addEventListener("click", () => {
      ejecutarComando(
        dom.modeControls,
        () => cambiarModo(button.dataset.mode),
        `Mode changed to ${button.textContent.trim()}.`,
        renderDispositivo,
      );
    });
  });

  dom.speedControls.querySelectorAll("button[data-speed]").forEach((button) => {
    button.addEventListener("click", () => {
      ejecutarComando(
        dom.speedControls,
        () => cambiarVelocidad(button.dataset.speed),
        `Irrigation speed changed to ${button.textContent.trim()}.`,
        renderDispositivo,
      );
    });
  });

  dom.valveControls.querySelectorAll("button[data-valve]").forEach((button) => {
    button.addEventListener("click", () => {
      ejecutarComando(
        dom.valveControls,
        () => cambiarValvula(button.dataset.valve),
        button.dataset.valve === "ABIERTA" ? "Valve opened." : "Valve closed.",
        renderDispositivo,
      );
    });
  });

  dom.sourceControls.querySelectorAll("button[data-source]").forEach((button) => {
    button.addEventListener("click", () => {
      dom.manualForm.dataset.dirty = "false";
      ejecutarComando(
        dom.sourceControls,
        () => cambiarFuenteAmbiente(button.dataset.source),
        `Environment source changed to ${button.textContent.trim()}.`,
        (response) => renderFuenteAmbiente(response.source),
      );
    });
  });

  dom.manualForm.addEventListener("input", () => {
    dom.manualForm.dataset.dirty = "true";
  });

  dom.manualForm.addEventListener("change", () => {
    dom.manualForm.dataset.dirty = "true";
  });

  dom.manualForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    limpiarErroresCampos();

    if (!dom.manualForm.checkValidity()) {
      dom.manualForm.reportValidity();
      return;
    }

    dom.manualFields.dataset.busy = "true";
    dom.manualFields.disabled = true;

    try {
      const response = await actualizarAmbienteManual({
        temperature: Number(dom.manualTemperature.value),
        ambient_humidity: Number(dom.manualHumidity.value),
        radiation: dom.manualRadiation.value,
        rain: dom.manualRain.value,
      });
      dom.manualForm.dataset.dirty = "false";
      renderAmbienteManual(response);
      mostrarFeedback("Manual environment conditions applied.");
    } catch (error) {
      marcarCamposInvalidos(error);
      mostrarFeedback(mensajeParaError(error), "error", 5000);
    } finally {
      dom.manualFields.dataset.busy = "false";
      await actualizarVista();
    }
  });
}

// 6. Polling

async function actualizarVista() {
  const previousConnection = dom.connectionStatus.dataset.state;
  const [deviceResult, environmentResult, manualEnvironmentResult] = await Promise.allSettled([
    obtenerDispositivo(),
    obtenerAmbiente(),
    obtenerAmbienteManual(),
  ]);

  if (deviceResult.status === "fulfilled") {
    renderDispositivo(deviceResult.value);
  }

  if (environmentResult.status === "fulfilled") {
    renderAmbiente(environmentResult.value);
  }

  if (environmentResult.status === "fulfilled") {
    if (environmentResult.value.source === "ALEATORIO") {
      dom.manualForm.dataset.dirty = "false";
      renderAmbienteManual(environmentResult.value);
    } else if (manualEnvironmentResult.status === "fulfilled") {
      renderAmbienteManual(manualEnvironmentResult.value);
    } else {
      renderAmbienteManual(environmentResult.value);
    }
  }

  const connected =
    deviceResult.status === "fulfilled" && environmentResult.status === "fulfilled";
  renderEstadoConexion(connected);

  if (!connected && previousConnection !== "disconnected") {
    mostrarFeedback(
      "Connection lost. Displayed values may be stale; retrying automatically.",
      "warning",
      5000,
    );
  } else if (connected && previousConnection === "disconnected") {
    mostrarFeedback("Connection restored. Live data is up to date.");
  }
}

function iniciarPolling() {
  let timerId = null;

  const poll = async () => {
    try {
      await actualizarVista();
    } finally {
      timerId = window.setTimeout(poll, POLLING_INTERVAL_MS);
    }
  };

  poll();

  return () => {
    if (timerId !== null) {
      window.clearTimeout(timerId);
    }
  };
}

// 7. Bootstrap

function iniciarApp() {
  registrarEventos();
  iniciarPolling();
}

iniciarApp();
