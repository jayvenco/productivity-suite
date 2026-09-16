from app.services.checklist import checklist_progress, toggle_checklist_line


def test_toggle_recognizes_missing_space_after_bracket():
    description = "- [ ]item zonder spatie"
    toggled = toggle_checklist_line(description, 0)
    assert toggled == "- [x] item zonder spatie"


def test_toggle_recognizes_missing_space_after_dash():
    description = "-[ ] item zonder spatie na streepje"
    toggled = toggle_checklist_line(description, 0)
    assert toggled == "-[x] item zonder spatie na streepje"


def test_toggle_standard_syntax_still_works():
    description = "- [ ] normaal item"
    toggled = toggle_checklist_line(description, 0)
    assert toggled == "- [x] normaal item"


def test_toggle_back_to_unchecked():
    description = "- [x] al gedaan"
    toggled = toggle_checklist_line(description, 0)
    assert toggled == "- [ ] al gedaan"


def test_checklist_progress_counts_done_items():
    description = "- [x] een\n- [ ] twee\nGewone tekst\n- [X] drie"
    done, total = checklist_progress(description)
    assert (done, total) == (2, 3)
