// Inklapbaar navigatiemenu voor mobiel: de sidebar schuift normaal buiten
// beeld (CSS, alleen onder de mobiele breakpoint) en klapt open als een
// paneel over de inhoud heen zodra op de hamburger-knop wordt geklikt.
document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.getElementById("mobile-menu-btn");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!menuBtn || !sidebar || !backdrop) return;

  // Desktop: het hele menu verbergen/tonen (keuze onthouden in localStorage; de vroege
  // inline-script in <head> zet data-sidebar al voor het eerste paint, zonder flits).
  const root = document.documentElement;
  const setHidden = (hidden) => {
    if (hidden) root.dataset.sidebar = "hidden";
    else delete root.dataset.sidebar;
    try {
      localStorage.setItem("sidebar-hidden", hidden ? "1" : "0");
    } catch (err) {
      /* localStorage geblokkeerd: de keuze geldt dan alleen tot de volgende pagina */
    }
  };
  const collapseBtn = document.getElementById("sidebar-collapse-btn");
  const showBtn = document.getElementById("sidebar-show-btn");
  if (collapseBtn) collapseBtn.addEventListener("click", () => setHidden(true));
  if (showBtn) showBtn.addEventListener("click", () => setHidden(false));

  function openMenu() {
    sidebar.classList.add("mobile-open");
    backdrop.classList.add("visible");
  }

  function closeMenu() {
    sidebar.classList.remove("mobile-open");
    backdrop.classList.remove("visible");
  }

  menuBtn.addEventListener("click", () => {
    if (sidebar.classList.contains("mobile-open")) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  backdrop.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });

  // Na het kiezen van een navigatie-link/thema mag het paneel weer dichtklappen
  // (anders blijft het openstaan bovenop de nieuwe pagina op mobiel).
  sidebar.addEventListener("click", (event) => {
    if (event.target.closest("a, button[type='submit']")) closeMenu();
  });
});
