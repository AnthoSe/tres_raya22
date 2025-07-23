let jugando = true;
let historial = [];
let modoAuto = false;

function renderTablero(tablero) {
  const table = document.getElementById("tablero");
  table.innerHTML = "";
  for (let i = 0; i < 3; i++) {
    const row = document.createElement("tr");
    for (let j = 0; j < 3; j++) {
      const cell = document.createElement("td");
      const value = tablero[i][j];
      if (value !== "b") {
        cell.innerText = value.toUpperCase();
        cell.classList.add(value);
      }
      row.appendChild(cell);
    }
    table.appendChild(row);
  }
}

function renderHistorial() {
  const div = document.getElementById("historial");
  if (historial.length === 0) {
    div.innerHTML = "<em>No hay jugadas aún.</em>";
    return;
  }
  div.innerHTML = historial
    .map(
      (h, idx) =>
        `#${idx + 1}: <b>${h.jugador.toUpperCase()}</b> (${h.modelo}) – ${h.razon}`
    )
    .join("<br>");
}

function guardarEstado(tableroActual) {
  const estado = {
    tablero: tableroActual,
    historial,
    jugando,
    modoAuto
  };
  sessionStorage.setItem("estado_tres_en_raya", JSON.stringify(estado));
}

function cargarEstado() {
  const guardado = sessionStorage.getItem("estado_tres_en_raya");
  if (!guardado) return false;

  try {
    const { tablero, historial: hist, jugando: jugandoGuardado, modoAuto: auto } = JSON.parse(guardado);
    historial = hist;
    jugando = jugandoGuardado;
    modoAuto = auto;
    renderTablero(tablero);
    renderHistorial();
    return true;
  } catch (e) {
    console.error("No se pudo restaurar el estado guardado:", e);
    return false;
  }
}

function jugarTurno() {
  if (!jugando) return;

  fetch("/jugar_turno", { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        mostrarError("Jugada inválida: " + data.error);
        jugando = false;
        return;
      }

      renderTablero(data.tablero);
      document.getElementById("razon").innerHTML = `Jugador <b>${data.jugador.toUpperCase()}</b> (${data.modelo}): ${data.razon}`;

      historial.push({
        jugador: data.jugador,
        razon: data.razon,
        modelo: data.modelo,
      });

      renderHistorial();

      if (data.ganador === "empate") {
        document.getElementById("razon").innerHTML += "<br><b>¡Empate!</b>";
        jugando = false;
      } else if (data.ganador) {
        document.getElementById("razon").innerHTML += `<br><b>Ganador: ${data.ganador.toUpperCase()}</b>`;
        jugando = false;
      }

      guardarEstado(data.tablero);

      if (modoAuto && jugando) {
        setTimeout(jugarTurno, 150);
      }
    })
    .catch((err) => {
      mostrarError("Error en la comunicación con el servidor.");
      console.error(err);
      jugando = false;
    });
}

function jugarAuto() {
  if (!jugando) return;
  modoAuto = true;
  jugarTurno();
}

function siguientePartida() {
  fetch("/siguiente_partida", { method: "POST" })
    .then((res) => res.json())
    .then(() => {
      jugando = true;
      modoAuto = false;
      historial = [];
      ocultarError();
      document.getElementById("razon").innerText = "";
      document.getElementById("historial").innerText = "";

      sessionStorage.removeItem("estado_tres_en_raya");

      fetch("/estado")
        .then((res) => res.json())
        .then((data) => renderTablero(data.tablero));
    })
    .catch((err) => {
      mostrarError("No se pudo reiniciar la partida.");
      console.error(err);
    });
}

function mostrarError(mensaje) {
  const errorDiv = document.getElementById("error-msg");
  errorDiv.textContent = mensaje;
  errorDiv.style.display = "block";
}

function ocultarError() {
  const errorDiv = document.getElementById("error-msg");
  errorDiv.style.display = "none";
}

function reiniciar() {
  fetch("/reiniciar", { method: "POST" })
    .then(() => {
      jugando = true;
      modoAuto = false;
      historial = [];
      document.getElementById("razon").innerText = "";
      document.getElementById("historial").innerText = "";
      ocultarError();

      sessionStorage.removeItem("estado_tres_en_raya");

      fetch("/estado")
        .then((res) => res.json())
        .then((data) => renderTablero(data.tablero));
    })
    .catch((err) => {
      mostrarError("No se pudo reiniciar el juego.");
      console.error(err);
    });
}

// Iniciar con tablero restaurado si existe
window.addEventListener("DOMContentLoaded", () => {
  const cargado = cargarEstado();
  if (!cargado) reiniciar();
});
