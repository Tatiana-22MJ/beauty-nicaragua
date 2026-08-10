/**
 * slots.js — Carga horarios libres desde /api/slots al cambiar la fecha.
 */
(() => {
  "use strict";

  function fillSlots(dateInput, timeSelect, preferred) {
    if (!dateInput || !timeSelect) return;
    const date = dateInput.value;
    if (!date) {
      timeSelect.innerHTML = '<option value="">Elegí una fecha</option>';
      return;
    }
    timeSelect.innerHTML = '<option value="">Cargando horarios…</option>';
    fetch(`/api/slots?date=${encodeURIComponent(date)}`)
      .then((r) => r.json())
      .then((data) => {
        timeSelect.innerHTML = "";
        if (!data.ok || !data.slots.length) {
          timeSelect.innerHTML = '<option value="">Sin horarios (cerrado u ocupado)</option>';
          return;
        }
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Selecciona horario";
        placeholder.disabled = true;
        placeholder.selected = !preferred;
        timeSelect.appendChild(placeholder);
        data.slots.forEach((hm) => {
          const opt = document.createElement("option");
          opt.value = hm;
          opt.textContent = hm;
          if (preferred && preferred === hm) opt.selected = true;
          timeSelect.appendChild(opt);
        });
      })
      .catch(() => {
        timeSelect.innerHTML = '<option value="">Error al cargar horarios</option>';
      });
  }

  function boot() {
    const dateInput = document.getElementById("preferred_date");
    const timeSelect = document.getElementById("preferred_time");
    if (!dateInput || !timeSelect) return;
    const preferred = timeSelect.dataset.preferred || "";
    dateInput.addEventListener("change", () => fillSlots(dateInput, timeSelect, ""));
    fillSlots(dateInput, timeSelect, preferred);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
