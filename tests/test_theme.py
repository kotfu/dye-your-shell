#
# Copyright (c) 2025 Jared Crapo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# pylint: disable=protected-access, missing-function-docstring, redefined-outer-name
# pylint: disable=missing-module-docstring, unused-variable

import pytest
import rich

from dye import Theme

SAMPLE_THEME = """
    [colors]
    background =  "#282a36"
    foreground =  "#f8f8f2"
    notyet =  "{{ colors.yellow }}"
    green =  "#50fa7b"
    orange =  "#ffb86c"
    pink =  "#ff79c6"
    purple =  "#bd93f9"
    yellow =  "#f1fa8c"
    background_high = "{{ colors.background }}"
    background_medium = "{{ color.background }}"
    background_low = "background"
    background_double1 = "{{ color.background_low }}"
    background_double2 = "background_medium"
    foreground_low = "{{ colors.unknown }}"

    [styles]
    notyet = "{{ styles.foreground }}"
    foreground = "{{ color.foreground }}"
    text = "bold {{ colors.foreground }} on {{ colors.background }}"
    text_high = "{{ styles.text }}"
    text_medium = "{{ style.text }}"
    text_low = "text"
    text_double1 = "{{ style.text_low }}"
    text_double2 = "text_medium"
    color1 = "#ff79c6"
    color2 = "{{ colors.unknown }}"
    color3 = ""
"""


@pytest.fixture
def sample_theme():
    return Theme.loads(SAMPLE_THEME)


#
# test load() and loads()
#
def test_load(tmp_path):
    # def test_load_from_args_theme_name(dye, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    themefile = tmp_path / "oxygen.toml"
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(SAMPLE_THEME)

    with open(themefile, encoding="utf8") as fvar:
        theme = Theme.load(fvar, filename=themefile)
    # Theme.load() uses the same code as Theme.loads(), so we don't
    # have to retest everything. If loads() works and load() can
    # open and read the file, load() will work too
    assert isinstance(theme.definition, dict)
    assert len(theme.definition) == 2
    assert len(theme.colors) == 14
    assert len(theme.styles) == 11


def test_loads(sample_theme):
    assert isinstance(sample_theme.definition, dict)
    assert len(sample_theme.definition) == 2


def test_loads_colors(sample_theme):
    assert isinstance(sample_theme.colors, dict)
    assert isinstance(sample_theme.colors["orange"], str)
    assert sample_theme.colors["orange"] == "#ffb86c"
    assert len(sample_theme.colors) == 14


def test_loads_styles(sample_theme):
    assert isinstance(sample_theme.styles, dict)
    assert isinstance(sample_theme.styles["text"], rich.style.Style)
    assert isinstance(sample_theme.styles["text_high"], rich.style.Style)
    assert isinstance(sample_theme.styles["color1"], rich.style.Style)
    assert len(sample_theme.styles) == 11


def test_loads_empty():
    theme = Theme.loads("")
    assert theme.definition == {}
    assert theme.colors == {}
    assert theme.styles == {}


def test_loads_none():
    theme = Theme.loads(None)
    assert theme.definition == {}
    assert theme.colors == {}
    assert theme.styles == {}


#
# test processing of colors
#
def test_color(sample_theme):
    assert sample_theme.colors["background"] == "#282a36"


def test_colors_reference(sample_theme):
    assert sample_theme.colors["background_high"] == sample_theme.colors["background"]


def test_color_reference(sample_theme):
    assert sample_theme.colors["background_medium"] == sample_theme.colors["background"]


def test_colors_bare_reference(sample_theme):
    assert sample_theme.colors["background_low"] == sample_theme.colors["background"]


def test_colors_double1_reference(sample_theme):
    assert (
        sample_theme.colors["background_double1"] == sample_theme.colors["background"]
    )


def test_colors_double2_reference(sample_theme):
    assert (
        sample_theme.colors["background_double2"] == sample_theme.colors["background"]
    )


def test_colors_unknown_reference(sample_theme):
    assert sample_theme.colors["foreground_low"] == ""


def test_colors_load_order(sample_theme):
    assert sample_theme.colors["notyet"] == ""


#
# test processing of styles
#
def test_style_color_ref(sample_theme):
    assert (
        sample_theme.styles["foreground"].color.name
        == sample_theme.colors["foreground"]
    )


def test_style_no_colors(sample_theme):
    assert sample_theme.styles["color1"].color.name == "#ff79c6"
    assert sample_theme.styles["color1"].color.triplet.hex == "#ff79c6"


def test_style_complex(sample_theme):
    assert sample_theme.styles["text"].color.name == "#f8f8f2"
    assert sample_theme.styles["text"].color.triplet.hex == "#f8f8f2"
    assert sample_theme.styles["text"].bgcolor.name == "#282a36"
    assert sample_theme.styles["text"].bgcolor.triplet.hex == "#282a36"
    assert sample_theme.styles["text_high"].color.name == "#f8f8f2"
    assert sample_theme.styles["text_high"].color.triplet.hex == "#f8f8f2"
    assert sample_theme.styles["text_high"].bgcolor.name == "#282a36"
    assert sample_theme.styles["text_high"].bgcolor.triplet.hex == "#282a36"


def test_style_reference(sample_theme):
    assert sample_theme.styles["text_medium"] == sample_theme.styles["text"]


def test_styles_bare_reference(sample_theme):
    assert sample_theme.styles["text_low"] == sample_theme.styles["text"]


def test_styles_double1_reference(sample_theme):
    assert sample_theme.styles["text_double1"] == sample_theme.styles["text"]


def test_styles_double2_reference(sample_theme):
    assert sample_theme.styles["text_double2"] == sample_theme.styles["text"]


def test_style_unknown_reference(sample_theme):
    assert not sample_theme.styles["color2"]
    assert isinstance(sample_theme.styles["color2"], rich.style.Style)


def test_styles_load_order(sample_theme):
    assert not sample_theme.styles["notyet"]
    assert isinstance(sample_theme.styles["notyet"], rich.style.Style)


def test_style_empty(sample_theme):
    assert not sample_theme.styles["color3"]
    assert isinstance(sample_theme.styles["color3"], rich.style.Style)
