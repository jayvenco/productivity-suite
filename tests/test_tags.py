from app.services.tags import generate_tag_color


def test_generate_tag_color_is_valid_hsl():
    color = generate_tag_color()
    assert color.startswith("hsl(")
    assert color.endswith(")")


def test_generate_tag_color_hue_within_range():
    for _ in range(20):
        color = generate_tag_color()
        hue = int(color[len("hsl(") : color.index(",")])
        assert 0 <= hue <= 359


def test_generate_tag_color_varies():
    # Met 20 trekkingen uit 360 tinten is de kans op identieke resultaten verwaarloosbaar.
    colors = {generate_tag_color() for _ in range(20)}
    assert len(colors) > 1
