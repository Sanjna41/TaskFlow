document.addEventListener("DOMContentLoaded", () => {
  const chart = document.getElementById("taskChart");
  if (chart && window.Chart) {
    new Chart(chart, {
      type: "doughnut",
      data: {
        labels: ["Completed", "Pending", "Overdue"],
        datasets: [{
          data: [chart.dataset.completed, chart.dataset.pending, chart.dataset.overdue],
          backgroundColor: ["#0f766e", "#2563eb", "#dc2626"]
        }]
      },
      options: { plugins: { legend: { position: "bottom" } } }
    });
  }

  let dragged = null;
  document.querySelectorAll(".task-card").forEach(card => {
    card.addEventListener("dragstart", () => { dragged = card; });
  });
  document.querySelectorAll(".kanban-column").forEach(column => {
    column.addEventListener("dragover", event => event.preventDefault());
    column.addEventListener("drop", () => {
      if (!dragged) return;
      const form = dragged.querySelector(".move-form");
      form.querySelector("input[name='status']").value = column.dataset.status;
      form.submit();
    });
  });
});
