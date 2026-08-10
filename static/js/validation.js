/**
 * validation.js — Validación client-side reutilizable (formularios auth + reserva).
 * Complementa validators.py del servidor; nunca reemplaza la validación backend.
 */
(() => {
  "use strict";

  // Patrones alineados con validators.py (incluye teléfonos +505).
  const EMAIL_RE = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
  const PHONE_RE = /^\+?[\d\s\-()]{8,20}$/;
  const USERNAME_RE = /^[a-zA-Z0-9_]{3,30}$/;

  /** Muestra u oculta el mensaje de error bajo un input. */
  function showError(input, message) {
    const errorEl = document.getElementById(`${input.id}-error`); // Span hermano.
    input.classList.toggle("invalid", !!message); // Borde rojo si hay error.
    input.classList.toggle("valid", !message && input.value.trim()); // Verde si OK.
    if (errorEl) errorEl.textContent = message || ""; // Texto accesible.
    input.setAttribute("aria-invalid", message ? "true" : "false"); // Screen readers.
  }

  /** Valida un campo según rules; retorna string de error o null. */
  function validateField(input, rules) {
    const value = input.value.trim(); // Valor normalizado.

    if (rules.required && !value) {
      return rules.message || "Campo obligatorio.";
    }

    if (rules.minLength && value.length < rules.minLength) {
      return rules.message || `Mínimo ${rules.minLength} caracteres.`;
    }

    if (rules.type === "email" && value && !EMAIL_RE.test(value)) {
      return rules.message || "Email no válido.";
    }

    if (rules.type === "phone" && value && !PHONE_RE.test(value)) {
      return rules.message || "Teléfono no válido (ej. +505 8877 2117).";
    }

    if (rules.type === "username" && value && !USERNAME_RE.test(value)) {
      return rules.message || "Usuario no válido.";
    }

    if (rules.type === "password" && value) {
      if (value.length < 8) return "Mínimo 8 caracteres.";
      if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) {
        return "Debe incluir letras y números.";
      }
    }

    if (rules.type === "date" && value) {
      const today = new Date().toISOString().split("T")[0];
      if (value < today) return "La fecha no puede ser pasada.";
    }

    // Confirmación de contraseña: compara con #password.
    if (input.id === "confirm_password") {
      const password = document.getElementById("password");
      if (password && value !== password.value) {
        return "Las contraseñas no coinciden.";
      }
    }

    return null; // Válido.
  }

  /** Engancha blur/input/submit a un formulario con un mapa name→rules. */
  function attachForm(form, fieldRules) {
    Object.entries(fieldRules).forEach(([name, rules]) => {
      const input = form.querySelector(`[name="${name}"]`);
      if (!input) return;

      input.addEventListener("blur", () => {
        showError(input, validateField(input, rules)); // Valida al salir del campo.
      });

      input.addEventListener("input", () => {
        if (input.classList.contains("invalid")) {
          showError(input, validateField(input, rules)); // Revalida mientras corrige.
        }
      });
    });

    form.addEventListener("submit", (e) => {
      let valid = true;

      Object.entries(fieldRules).forEach(([name, rules]) => {
        const input = form.querySelector(`[name="${name}"]`);
        if (!input) return;
        const error = validateField(input, rules);
        showError(input, error);
        if (error) valid = false;
      });

      if (!valid) e.preventDefault(); // Bloquea el POST si hay errores.
    });
  }

  // API pública usada por main.js y páginas auth.
  window.BeautyValidation = { attachForm, validateField, showError };

  // Auto-enganche en login/registro cuando el DOM está listo.
  document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
      attachForm(registerForm, {
        full_name: { required: true, minLength: 2, message: "Nombre: mínimo 2 caracteres." },
        username: { required: true, type: "username", message: "Usuario: 3-30 caracteres alfanuméricos." },
        email: { required: true, type: "email", message: "Introduce un email válido." },
        phone: { required: true, type: "phone", message: "Teléfono no válido (ej. +505…)." },
        password: { required: true, type: "password", message: "Contraseña no válida." },
        confirm_password: { required: true, type: "password", message: "Las contraseñas no coinciden." },
      });
    }

    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
      attachForm(loginForm, {
        identifier: { required: true, message: "Introduce tu usuario o email." },
        password: { required: true, message: "Introduce tu contraseña." },
      });
    }
  });
})();
