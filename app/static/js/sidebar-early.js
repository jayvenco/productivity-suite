// Draait synchroon in <head>: zet het "menu verborgen"-attribuut vóór het eerste paint, zodat er
// geen flits van het menu is (zie de verbergknop in app/static/js/mobile-nav.js).
try {
  if (localStorage.getItem("sidebar-hidden") === "1") document.documentElement.dataset.sidebar = "hidden";
} catch (e) {
  /* localStorage geblokkeerd: menu blijft zichtbaar */
}
