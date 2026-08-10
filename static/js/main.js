/**
 * main.js — Navegación, reveals buttery-smooth, scrolltelling y validación de reserva.
 * Cada bloque está documentado: qué escucha, qué anima y por qué.
 */
(() => {
  "use strict"; // Evita variables globales accidentales y errores silenciosos.

  // --- Referencias al DOM (null-safe: solo actúan si el elemento existe) ---
  const nav = document.querySelector(".site-nav"); // Barra de navegación sticky.
  const toggle = document.getElementById("navToggle"); // Botón hamburguesa móvil.
  const menu = document.getElementById("navMenu"); // Lista de enlaces del menú.
  const dateInput = document.getElementById("preferred_date"); // Input date del booking.

  // --- Sombra en nav al hacer scroll (feedback visual buttery) ---
  if (nav) {
    // passive: true = el scroll no espera al listener → más fluido en móvil.
    window.addEventListener("scroll", () => {
      // Añade .scrolled cuando el usuario bajó más de 20px.
      nav.classList.toggle("scrolled", window.scrollY > 20);
    }, { passive: true });
  }

  // --- Menú móvil: abre/cierra y sincroniza aria-expanded ---
  if (toggle && menu) {
    toggle.addEventListener("click", () => {
      const isOpen = menu.classList.toggle("open"); // Alterna clase CSS.
      toggle.setAttribute("aria-expanded", String(isOpen)); // Accesibilidad.
    });

    // Al tocar un enlace interno, cierra el menú automáticamente.
    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        menu.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // --- Fecha mínima = hoy (impide reservar en el pasado) ---
  if (dateInput) {
    dateInput.setAttribute("min", new Date().toISOString().split("T")[0]);
  }

  // --- Reveal on scroll: animaciones buttery con IntersectionObserver ---
  const reveals = document.querySelectorAll(".reveal");
  if (reveals.length && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) { // El elemento entró al viewport.
            entry.target.classList.add("visible"); // Dispara transición CSS.
            observer.unobserve(entry.target); // Solo una vez (mejor rendimiento).
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" } // Dispara un poco antes del centro.
    );
    reveals.forEach((el) => observer.observe(el)); // Observa cada .reveal.
  } else {
    // Fallback sin IntersectionObserver: muestra todo visible.
    reveals.forEach((el) => el.classList.add("visible"));
  }

  // --- Scrolltelling: capítulos sticky que cambian imagen/texto al scrollear ---
  const chapters = document.querySelectorAll(".scrolltell-chapter"); // Triggers invisibles.
  const stageImg = document.getElementById("scrolltellImage"); // Imagen del escenario.
  const caption = document.getElementById("scrolltellCaption"); // Bloque de texto.

  if (chapters.length && stageImg && caption && "IntersectionObserver" in window) {
    const chapterObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return; // Ignora salidas del viewport.
          const chapter = entry.target; // Artículo con data-* del capítulo.
          const step = chapter.dataset.step || ""; // Ej. "01".
          const title = chapter.dataset.title || ""; // Título narrativo.
          const text = chapter.dataset.text || ""; // Párrafo de apoyo.
          const img = chapter.dataset.img || ""; // URL de imagen local.

          // Crossfade suave: baja opacidad → cambia src → sube opacidad.
          stageImg.style.opacity = "0.35";
          window.setTimeout(() => {
            if (img) stageImg.src = img; // Cambia la foto del capítulo.
            stageImg.alt = title; // Actualiza alt accesible.
            caption.innerHTML = `
              <span class="scrolltell-step">${step}</span>
              <h3>${title}</h3>
              <p>${text}</p>
            `;
            stageImg.style.opacity = "1"; // Vuelve a full opacity.
          }, 220); // Delay alineado con transition CSS (~0.25s).
        });
      },
      { threshold: 0.55 } // El capítulo debe ocupar ~55% del viewport para activarse.
    );
    chapters.forEach((ch) => chapterObserver.observe(ch));
  }

  // --- FAQ accordion: una sola pregunta abierta a la vez ---
  const faqItems = document.querySelectorAll(".faq-item");
  faqItems.forEach((item) => {
    const button = item.querySelector(".faq-question");
    const answer = item.querySelector(".faq-answer");
    if (!button || !answer) return;

    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") === "true";
      faqItems.forEach((other) => {
        const otherButton = other.querySelector(".faq-question");
        const otherAnswer = other.querySelector(".faq-answer");
        if (!otherButton || !otherAnswer) return;
        otherButton.setAttribute("aria-expanded", "false");
        otherAnswer.style.maxHeight = "0px";
      });
      button.setAttribute("aria-expanded", String(!expanded));
      answer.style.maxHeight = expanded ? "0px" : `${answer.scrollHeight}px`;
    });
    answer.style.maxHeight = "0px";
  });

  // --- Gallery lightbox modal ---
  const galleryFigures = document.querySelectorAll(".gallery-item");
  const modal = document.createElement("div");
  modal.className = "gallery-modal";
  modal.setAttribute("hidden", "hidden");
  modal.innerHTML = `
    <div class="gallery-modal-backdrop" role="presentation"></div>
    <div class="gallery-modal-card" role="dialog" aria-modal="true" aria-label="Vista ampliada de galería">
      <button type="button" class="gallery-modal-close" aria-label="Cerrar vista ampliada">×</button>
      <img src="" alt="Vista ampliada de Beauty Nicaragua" class="gallery-modal-image">
    </div>
  `;
  document.body.appendChild(modal);

  const modalImage = modal.querySelector(".gallery-modal-image");
  const closeModal = () => {
    modal.setAttribute("hidden", "hidden");
    document.body.classList.remove("modal-open");
  };
  modal.querySelector(".gallery-modal-close").addEventListener("click", closeModal);
  modal.querySelector(".gallery-modal-backdrop").addEventListener("click", closeModal);

  galleryFigures.forEach((figure) => {
    const open = () => {
      const full = figure.dataset.full || figure.querySelector("img")?.src || "";
      if (!modalImage || !full) return;
      modalImage.src = full;
      modal.removeAttribute("hidden");
      document.body.classList.add("modal-open");
    };
    figure.addEventListener("click", open);
    figure.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hasAttribute("hidden")) {
      closeModal();
    }
  });

  // --- Validación del formulario de reserva (si BeautyValidation está cargado) ---
  const bookingForm = document.getElementById("bookingForm");
  if (bookingForm && window.BeautyValidation) {
    window.BeautyValidation.attachForm(bookingForm, {
      full_name: { required: true, minLength: 2, message: "Nombre: mínimo 2 caracteres." },
      email: { required: true, type: "email", message: "Introduce un email válido." },
      phone: { required: true, type: "phone", message: "Teléfono no válido (ej. +505 8877 2117)." },
      service_id: { required: true, message: "Selecciona un servicio." },
      preferred_date: { required: true, type: "date", message: "Indica una fecha válida." },
    });
  }
})();
