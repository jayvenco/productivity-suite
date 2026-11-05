"""Lettertypen en groottes voor het scratchpad. De Google-lettertypen worden al door base.html
geladen; de rest zijn systeemlettertypen."""

from __future__ import annotations

# (id, label, css font-family; "" = zoals de rest van de app)
SCRATCHPAD_FONTS = [
    ("system", "Standaard (zoals de app)", ""),
    ("segoe-ui", "Segoe UI", '"Segoe UI", system-ui, -apple-system, sans-serif'),
    ("arial", "Arial", "Arial, Helvetica, sans-serif"),
    ("georgia", "Georgia (serif)", "Georgia, 'Times New Roman', serif"),
    ("inter", "Inter", '"Inter", sans-serif'),
    ("roboto", "Roboto", '"Roboto", sans-serif'),
    ("open-sans", "Open Sans", '"Open Sans", sans-serif'),
    ("lato", "Lato", '"Lato", sans-serif'),
    ("poppins", "Poppins", '"Poppins", sans-serif'),
    ("nunito", "Nunito", '"Nunito", sans-serif'),
    ("source-sans", "Source Sans 3", '"Source Sans 3", sans-serif'),
    ("fira-sans", "Fira Sans", '"Fira Sans", sans-serif'),
    ("dm-sans", "DM Sans", '"DM Sans", sans-serif'),
    ("alegreya-sans", "Alegreya Sans", '"Alegreya Sans", sans-serif'),
    ("exo-2", "Exo 2", '"Exo 2", sans-serif'),
    ("merriweather", "Merriweather (serif)", '"Merriweather", serif'),
    ("bitter", "Bitter (serif)", '"Bitter", serif'),
    ("playfair-display", "Playfair Display (serif)", '"Playfair Display", serif'),
    ("hack", "Hack (monospace)", '"Hack", monospace'),
    ("jetbrains-mono", "JetBrains Mono (monospace)", '"JetBrains Mono", monospace'),
    ("fira-code", "Fira Code (monospace)", '"Fira Code", monospace'),
    ("consolas", "Consolas (monospace)", 'Consolas, "SF Mono", ui-monospace, monospace'),
]
SCRATCHPAD_FONT_IDS = {font_id for font_id, _, _ in SCRATCHPAD_FONTS}
SCRATCHPAD_FONT_SIZES = [12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32]
DEFAULT_FONT = "system"
DEFAULT_SIZE = 16
