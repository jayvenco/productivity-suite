// Registreert de service worker (alleen mogelijk in een beveiligde context: HTTPS of localhost).
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {
      /* registreren mislukt: de app werkt gewoon als normale website */
    });
  });
}
