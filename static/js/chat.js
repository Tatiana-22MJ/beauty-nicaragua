/**
 * chat.js — Chat en tiempo real (Socket.IO) SOLO para usuarias autenticadas.
 * Si data-authenticated="false", muestra gate de login y no abre socket.
 */
(() => {
  "use strict"; // Modo estricto ES5+.

  // Contenedor del widget con flags de autenticación inyectados por Jinja.
  const widget = document.getElementById("chatWidget");
  const toggle = document.getElementById("chatToggle"); // Botón flotante.
  const panel = document.getElementById("chatPanel"); // Panel del chat.
  const closeBtn = document.getElementById("chatClose"); // Botón X.
  const form = document.getElementById("chatForm"); // Formulario (solo si auth).
  const input = document.getElementById("chatInput"); // Campo de texto.
  const messages = document.getElementById("chatMessages"); // Log de mensajes.

  if (!toggle || !panel) return; // Sin UI de chat → salir.

  // Lee si la usuaria está autenticada desde el atributo data-*.
  const isAuthenticated = widget?.dataset.authenticated === "true";
  const loginUrl = widget?.dataset.loginUrl || "/login"; // URL de login.
  let socket = null; // Instancia Socket.IO (lazy).
  let isOpen = false; // Estado abierto/cerrado del panel.

  /** Inicializa la conexión WebSocket solo si hay sesión autenticada. */
  function initSocket() {
    if (!isAuthenticated) return; // Anónimos no conectan.
    if (typeof io === "undefined") return; // CDN aún no cargó.
    if (socket) return; // Evita conexiones duplicadas.

    socket = io({ transports: ["websocket", "polling"] }); // Preferir WS, fallback polling.

    // El servidor aceptó la conexión autenticada.
    socket.on("connected", (data) => {
      // Saludo opcional si el server envía el primer nombre.
      if (data && data.user) {
        // No spamea: solo deja constancia en consola de depuración.
        console.debug("Chat conectado como", data.user);
      }
    });

    // El servidor rechazó por falta de auth (sesión expirada, etc.).
    socket.on("auth_required", (data) => {
      removeTyping();
      appendMessage(
        (data && data.message) || "Debés iniciar sesión para chatear.",
        "bot"
      );
      // Ofrece enlace de login dentro del hilo.
      appendMessage(`Ir a iniciar sesión: ${loginUrl}`, "bot");
    });

    // Respuesta contextual de Bella.
    socket.on("bot_message", (data) => {
      removeTyping();
      appendMessage(data.message, "bot");
    });
  }

  /** Inserta un mensaje en el log (escapa HTML para prevenir XSS). */
  function appendMessage(text, type) {
    const div = document.createElement("div");
    div.className = `chat-msg chat-msg-${type}`;
    div.innerHTML = `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight; // Autoscroll al último mensaje.
  }

  /** Muestra indicador "Bella está escribiendo…". */
  function showTyping() {
    removeTyping();
    const div = document.createElement("div");
    div.className = "chat-msg chat-msg-bot chat-msg-typing";
    div.id = "chatTyping";
    div.innerHTML = "<p>Bella está escribiendo<span>...</span></p>";
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  /** Quita el indicador de escritura si existe. */
  function removeTyping() {
    const typing = document.getElementById("chatTyping");
    if (typing) typing.remove();
  }

  /** Escapa <, >, & para insertar texto seguro en innerHTML. */
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str; // textContent no interpreta HTML.
    return div.innerHTML; // Devuelve entidades escapadas.
  }

  /** Abre el panel; si no hay auth, solo muestra el gate (sin socket). */
  function openChat() {
    isOpen = true;
    panel.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    if (isAuthenticated) {
      if (!socket) initSocket(); // Conecta al abrir (lazy).
      if (input) input.focus(); // Foco en el campo.
    }
  }

  /** Cierra el panel del chat. */
  function closeChat() {
    isOpen = false;
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
  }

  // Click en el FAB Bella.
  toggle.addEventListener("click", () => {
    isOpen ? closeChat() : openChat();
  });

  // Click en la X.
  if (closeBtn) closeBtn.addEventListener("click", closeChat);

  // Envío de mensaje (solo existe el form si la usuaria está autenticada).
  if (form && input && isAuthenticated) {
    form.addEventListener("submit", (e) => {
      e.preventDefault(); // No recarga la página.
      const text = input.value.trim();
      if (!text || text.length > 500) return; // Validación cliente.

      appendMessage(text, "user"); // Pinta el mensaje propio.
      input.value = ""; // Limpia el input.
      showTyping(); // Feedback inmediato.

      if (socket && socket.connected) {
        socket.emit("send_message", { message: text }); // Emite al servidor.
      } else {
        // Reintenta conexión si se cayó el socket.
        setTimeout(() => {
          removeTyping();
          appendMessage("Reconectando… Intentá de nuevo en un momento.", "bot");
          initSocket();
        }, 800);
      }
    });
  }

  // Precarga el socket al cargar el DOM si ya hay sesión.
  document.addEventListener("DOMContentLoaded", () => {
    if (isAuthenticated) initSocket();
  });
})();
