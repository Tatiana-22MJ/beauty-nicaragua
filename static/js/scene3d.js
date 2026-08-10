/**
 * scene3d.js — Renderizado 3D interactivo (Three.js) en el hero.
 * Crea una esfera de partículas que reacciona al mouse/touch (buttery 60fps).
 */
(() => {
  "use strict";

  // Espera a que el DOM y Three.js (defer) estén listos.
  function boot() {
    const canvas = document.getElementById("scene3d"); // Lienzo del hero.
    if (!canvas || typeof THREE === "undefined") return; // Sin canvas o sin lib → noop.

    // --- Tamaño del contenedor padre (hero-stage) ---
    const parent = canvas.parentElement;
    const getSize = () => ({
      w: parent.clientWidth || 420, // Ancho disponible.
      h: parent.clientHeight || 520, // Alto disponible.
    });

    let { w, h } = getSize(); // Dimensiones iniciales.

    // --- Escena, cámara y renderer WebGL ---
    const scene = new THREE.Scene(); // Contenedor 3D.
    const camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 100); // FOV 42°.
    camera.position.z = 4.2; // Aleja la cámara para ver la esfera.

    const renderer = new THREE.WebGLRenderer({
      canvas, // Usa el <canvas> existente.
      alpha: true, // Fondo transparente (se ve la foto debajo).
      antialias: true, // Bordes suaves.
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); // Retina cap 2x.
    renderer.setSize(w, h, false); // Ajusta buffer sin pelear con CSS.

    // --- Geometría de partículas (esfera) ---
    const count = 900; // Cantidad de puntos (equilibrio belleza/perf).
    const positions = new Float32Array(count * 3); // x,y,z por partícula.
    for (let i = 0; i < count; i++) {
      // Distribución uniforme aproximada en esfera unitaria.
      const r = 1.15 + Math.random() * 0.35; // Radio con variación.
      const theta = Math.random() * Math.PI * 2; // Ángulo azimutal.
      const phi = Math.acos(2 * Math.random() - 1); // Ángulo polar.
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta); // X.
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta); // Y.
      positions[i * 3 + 2] = r * Math.cos(phi); // Z.
    }

    const geometry = new THREE.BufferGeometry(); // Geometría de buffer.
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      size: 0.035, // Tamaño de cada punto.
      color: 0xe0569a, // Rosa de la marca Beauty.
      transparent: true, // Permite opacidad.
      opacity: 0.85, // Semitransparente sobre la foto.
      depthWrite: false, // Evita artefactos de profundidad.
      blending: THREE.AdditiveBlending, // Brillo suave al solaparse.
    });

    const points = new THREE.Points(geometry, material); // Mesh de partículas.
    scene.add(points); // Añade a la escena.

    // Anillo decorativo (torus) para dar volumen legible.
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.35, 0.02, 16, 100),
      new THREE.MeshBasicMaterial({ color: 0x5b8def, transparent: true, opacity: 0.55 })
    );
    ring.rotation.x = Math.PI / 2.6; // Inclina el anillo.
    scene.add(ring);

    // --- Interacción: pointer normalizado (-1…1) ---
    const pointer = { x: 0, y: 0 }; // Objetivo de rotación.
    const onPointer = (clientX, clientY) => {
      const rect = canvas.getBoundingClientRect(); // Posición del canvas en pantalla.
      pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1; // -1 izq … +1 der.
      pointer.y = -(((clientY - rect.top) / rect.height) * 2 - 1); // -1 abajo … +1 arriba.
    };

    window.addEventListener("pointermove", (e) => onPointer(e.clientX, e.clientY), { passive: true });
    window.addEventListener("touchmove", (e) => {
      if (e.touches[0]) onPointer(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });

    // --- Resize: mantiene el aspect ratio al cambiar el layout ---
    window.addEventListener("resize", () => {
      ({ w, h } = getSize());
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    });

    // --- Loop de animación (requestAnimationFrame = buttery smooth) ---
    const clock = new THREE.Clock(); // Tiempo delta preciso.
    function animate() {
      requestAnimationFrame(animate); // Programa el siguiente frame.
      const t = clock.getElapsedTime(); // Segundos desde el start.

      // Rotación idle + lerp hacia el pointer (suavizado).
      points.rotation.y += 0.0025; // Giro continuo lento.
      points.rotation.x += (pointer.y * 0.35 - points.rotation.x) * 0.04; // Lerp X.
      points.rotation.y += (pointer.x * 0.45 - (points.rotation.y % (Math.PI * 2))) * 0.02;

      ring.rotation.z = t * 0.25; // El anillo gira en Z.
      ring.rotation.x = Math.PI / 2.6 + pointer.y * 0.2; // Responde al mouse.

      // Pulso sutil de escala (respiración).
      const s = 1 + Math.sin(t * 1.2) * 0.03;
      points.scale.set(s, s, s);

      renderer.render(scene, camera); // Dibuja el frame.
    }
    animate(); // Arranca el loop.
  }

  // Three.js se carga con defer: esperamos window.load o DOMContentLoaded tardío.
  if (document.readyState === "complete") {
    boot();
  } else {
    window.addEventListener("load", boot);
  }
})();
