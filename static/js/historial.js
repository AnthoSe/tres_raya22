// Mostrar u ocultar el panel lateral de rúbrica
function toggleRubrica() {
  const panel = document.getElementById('rubricaPanel');
  const expanded = panel.classList.toggle('active');
  panel.setAttribute('aria-hidden', !expanded);
}

// Filtro en tiempo real
document.addEventListener('DOMContentLoaded', () => {
  const filtroInput = document.getElementById("filtro");
  filtroInput.addEventListener("input", function () {
    const val = this.value.toLowerCase();
    document.querySelectorAll("tbody tr").forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(val) ? "" : "none";
    });
  });

  // Radar Chart
  const dimensiones = window.dimensiones || [];
  const promedios = window.promedios || {};
  const dataValores = dimensiones.map(dim => promedios[dim] || 0);

  const config = {
    type: 'radar',
    data: {
      labels: dimensiones,
      datasets: [{
        label: 'Puntaje promedio',
        data: dataValores,
        fill: true,
        backgroundColor: 'rgba(54, 162, 235, 0.25)',
        borderColor: 'rgb(54, 162, 235)',
        pointBackgroundColor: 'rgb(54, 162, 235)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(54, 162, 235)'
      }]
    },
    options: {
      scales: {
        r: {
          beginAtZero: true,
          min: 0,
          max: 3,
          ticks: {
            stepSize: 1
          }
        }
      },
      plugins: {
        legend: {
          labels: {
            font: {
              size: 14
            }
          }
        }
      }
    }
  };

  const canvas = document.getElementById('graficoRadar');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, config);
  }
});
