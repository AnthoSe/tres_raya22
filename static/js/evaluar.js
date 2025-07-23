// Mostrar/ocultar panel lateral de rúbrica
function toggleRubrica() {
  const panel = document.getElementById("rubricaPanel");
  panel.classList.toggle("open");
}

// Validación del formulario antes de enviar
function validarFormulario() {
  const form = document.querySelector('form[action="/guardar_evaluacion"]');
  if (!form) return true;

  const dimensiones = [
    "Comprensión de Reglas",
    "Validez y Legalidad",
    "Razonamiento Estratégico",
    "Factualidad",
    "Coherencia Explicativa",
    "Claridad Lingüística",
    "Adaptabilidad",
  ];

  for (const dim of dimensiones) {
    const radios = document.querySelectorAll(
      `input[name="rubrica[${dim}]"]`
    );
    const algunoMarcado = [...radios].some((r) => r.checked);
    if (!algunoMarcado) {
      alert(`Por favor, evalúa la dimensión: "${dim}"`);
      return false;
    }
  }

  const razonEl = document.getElementById("razon");
  if (razonEl && razonEl.value.trim().length < 3) {
    alert("Por favor, escribe una explicación más completa.");
    return false;
  }

  return true;
}

// Renderiza el tablero en pantalla
function renderTablero(tablero, movimiento) {
  const contenedor = document.getElementById("tablero-dinamico");
  contenedor.innerHTML = "";

  const table = document.createElement("table");
  table.className = "tablero";

  for (let i = 0; i < 3; i++) {
    const row = document.createElement("tr");
    for (let j = 0; j < 3; j++) {
      const cell = document.createElement("td");
      const value = tablero[i][j];

      if (value !== "b") {
        cell.innerText = value.toUpperCase();
        cell.classList.add(value); // clase 'x' o 'o'
      }

      // Resaltar celda marcada si coincide con el movimiento
      if (
        movimiento &&
        movimiento[0] === "mark" &&
        movimiento[1] - 1 === i &&
        movimiento[2] - 1 === j
      ) {
        cell.classList.add("marcada");
      }

      row.appendChild(cell);
    }
    table.appendChild(row);
  }

  contenedor.appendChild(table);
}

// Cargar info textual de la jugada
function cargarInfoJugada() {
  fetch("/info_jugada_sesion")
    .then((res) => res.json())
    .then((data) => {
      const contenedor = document.getElementById("info-jugada");

      if (data.error) {
        contenedor.innerHTML = "<p>No hay jugadas aún.</p>";
      } else {
        contenedor.innerHTML = `
          <p><strong>Jugador:</strong> ${data.jugador.toUpperCase()}</p>
          <p><strong>Modelo:</strong> ${data.modelo}</p>
          <p><strong>Movimiento:</strong> 
            ${
              Array.isArray(data.movimiento) && data.movimiento[0] === "mark"
                ? `Marcar fila ${data.movimiento[1]}, columna ${data.movimiento[2]}`
                : JSON.stringify(data.movimiento)
            }
          </p>
        `;
      }
    })
    .catch((err) => {
      console.error("Error al cargar info de la jugada:", err);
      const contenedor = document.getElementById("info-jugada");
      contenedor.innerHTML =
        "<p class='text-danger'>Error al cargar información de la jugada.</p>";
    });
}

// Inicialización: cargar estado actual del tablero + info jugada
document.addEventListener("DOMContentLoaded", () => {
  fetch("/estado")
    .then((res) => res.json())
    .then((data) => {
      renderTablero(data.tablero, data.movimiento);
      cargarInfoJugada();
    })
    .catch((err) => {
      console.error("Error al obtener el estado:", err);
    });
});
