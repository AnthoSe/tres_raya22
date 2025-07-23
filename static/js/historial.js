// Función para mostrar/ocultar el panel lateral de rúbrica
function toggleRubrica() {
  const panel = document.getElementById('rubricaPanel');
  const expanded = panel.classList.toggle('active');
  panel.setAttribute('aria-hidden', !expanded);
}

// Filtro en tiempo real para la tabla historial
document.addEventListener('DOMContentLoaded', () => {
  const filtroInput = document.getElementById("filtro");
  filtroInput.addEventListener("input", function () {
    const val = this.value.toLowerCase();
    document.querySelectorAll("tbody tr").forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(val) ? "" : "none";
    });
  });
});
