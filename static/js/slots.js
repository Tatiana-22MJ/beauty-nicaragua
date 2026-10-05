/**
 * slots.js — Carga horarios libres desde /api/slots al cambiar la fecha.
 * La agenda considera la duración del servicio/pack elegido (p.ej. 120 min
 * de coloración bloquean dos huecos), por eso se reconsulta al cambiarlo.
 */
(() => {
  "use strict";

  function queryString(date) {
    const params = new URLSearchParams({ date });
    ["service_id", "package_id"].forEach((id) => {
      const el = document.getElementById(id);
      if (el && el.value) params.set(id, el.value);
    });
    return params.toString();
  }

  function fillSlots(dateInput, timeSelect, preferred) {
    if (!dateInput || !timeSelect) return;
    const date = dateInput.value;
    if (!date) {
      timeSelect.innerHTML = '<option value="">Elegí una fecha</option>';
      return;
    }
    timeSelect.innerHTML = '<option value="">Cargando horarios…</option>';
    fetch(`/api/slots?${queryString(date)}`)
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
    const reload = () => fillSlots(dateInput, timeSelect, "");
    dateInput.addEventListener("change", reload);
    // Cambiar de servicio/pack altera la duración → reconsulta los horarios.
    ["service_id", "package_id"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener("change", reload);
    });
    fillSlots(dateInput, timeSelect, preferred);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
