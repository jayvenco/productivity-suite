from app.services.tags import generate_tag_color


def test_generate_tag_color_is_deterministic():
    assert generate_tag_color("werk") == generate_tag_color("werk")


def test_generate_tag_color_is_case_and_whitespace_insensitive():
    assert generate_tag_color("Werk") == generate_tag_color(" werk ")


def test_generate_tag_color_differs_between_names():
    assert generate_tag_color("werk") != generate_tag_color("prive")


def test_generate_tag_color_is_valid_hsl():
    color = generate_tag_color("urgent")
    assert color.startswith("hsl(")
    assert color.endswith(")")
