from __future__ import annotations

import re

CHECKLIST_LINE = re.compile(r"^(\s*[-*]\s+)\[([ xX])\](\s+.*)$")


def toggle_checklist_line(description: str, line_index: int) -> str:
    """Wisselt '- [ ]' <-> '- [x]' om op de gegeven regel (0-based) van de beschrijving."""
    lines = description.splitlines()
    if not (0 <= line_index < len(lines)):
        return description

    match = CHECKLIST_LINE.match(lines[line_index])
    if not match:
        return description

    prefix, mark, rest = match.groups()
    new_mark = " " if mark.lower() == "x" else "x"
    lines[line_index] = f"{prefix}[{new_mark}]{rest}"
    return "\n".join(lines)


def is_checklist_line(line: str) -> bool:
    return bool(CHECKLIST_LINE.match(line))


def checklist_progress(description: str) -> tuple[int, int]:
    """Geeft (aantal afgevinkt, totaal) checklist-items terug."""
    lines = description.splitlines()
    matches = [CHECKLIST_LINE.match(line) for line in lines]
    matches = [m for m in matches if m]
    done = sum(1 for m in matches if m.group(2).lower() == "x")
    return done, len(matches)


def render_description_html(description: str, card_id: int, render_markdown) -> str:
    """Rendert een kaartbeschrijving waarbij '- [ ]'/'- [x]'-regels aanklikbare
    checkboxes worden en de rest gewoon door de markdown-renderer gaat."""
    if not description:
        return ""

    lines = description.splitlines()
    html_parts: list[str] = []
    buffer: list[str] = []

    def flush_buffer() -> None:
        if buffer:
            html_parts.append(render_markdown("\n".join(buffer)))
            buffer.clear()

    for idx, line in enumerate(lines):
        match = CHECKLIST_LINE.match(line)
        if match is None:
            buffer.append(line)
            continue

        flush_buffer()
        _, mark, rest = match.groups()
        checked = mark.lower() == "x"
        label_html = render_markdown(rest.strip())
        # render_markdown wrapt in <p>...</p>; voor een inline checklist-item willen we dat niet.
        if label_html.startswith("<p>"):
            label_html = label_html[len("<p>") :].rsplit("</p>", 1)[0]
        html_parts.append(
            '<label class="checklist-item{done_class}">'
            '<input type="checkbox" data-card-id="{card_id}" data-line-index="{idx}" {checked}>'
            "<span>{label}</span></label>".format(
                done_class=" done" if checked else "",
                card_id=card_id,
                idx=idx,
                checked="checked" if checked else "",
                label=label_html,
            )
        )

    flush_buffer()
    return "".join(html_parts)
