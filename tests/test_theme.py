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

#
# test style and variable processing on initialization
#
STATIC_THEME = """
    [palette]
    background =  "#282a36"
    foreground =  "#f8f8f2"
    notyet =  "{{ palette.yellow }}"
    green =  "#50fa7b"
    orange =  "#ffb86c"
    pink =  "#ff79c6"
    purple =  "#bd93f9"
    yellow =  "#f1fa8c"
    background_high = "{{ palette.background }}"
    foreground_low = "{{ palette.unknown }}"

    [elements]
    notyet = "{{ elements.foreground }}"
    foreground = "{{ palette.foreground }}"
    text = "bold {{ palette.foreground }} on {{ palette.background }}"
    text_high = "{{ elements.text }}"
    color1 = "#ff79c6"
    color2 = "{{ palette.unknown }}"
    color3 = ""
"""


@pytest.fixture
def static_theme():
    return Theme.loads(STATIC_THEME)


def test_load(tmp_path):
    # def test_load_from_args_theme_name(dye, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    themefile = tmp_path / "oxygen.toml"
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(STATIC_THEME)

    with open(themefile, encoding="utf8") as fvar:
        theme = Theme.load(fvar, filename=themefile)
    # Theme.load() uses the same code as Theme.loads(), so we don't
    # have to retest everything. If loads() works and load() can
    # open and read the file, load() will work too
    assert len(theme.palette) == 10
    assert len(theme.elements) == 7


def test_loads_palette(static_theme):
    assert isinstance(static_theme.palette, dict)
    assert isinstance(static_theme.palette["orange"], str)
    assert static_theme.palette["orange"] == "#ffb86c"
    assert len(static_theme.palette) == 10


def test_loads_elements():
    theme = Theme.loads(STATIC_THEME)
    assert isinstance(theme.elements, dict)
    assert isinstance(theme.elements["text"], rich.style.Style)
    assert isinstance(theme.elements["text_high"], rich.style.Style)
    assert isinstance(theme.elements["color1"], rich.style.Style)
    assert len(theme.elements) == 7


def test_loads_empty():
    theme = Theme.loads("")
    assert theme.definition == {}
    assert theme.palette == {}
    assert theme.elements == {}


def test_palette_reference(static_theme):
    assert static_theme.palette["background_high"] == static_theme.palette["background"]


def test_palette_unknown_reference(static_theme):
    assert static_theme.palette["foreground_low"] == ""


def test_palette_load_order(static_theme):
    assert static_theme.palette["notyet"] == ""


def test_element_no_palette(static_theme):
    assert static_theme.elements["color1"].color.name == "#ff79c6"
    assert static_theme.elements["color1"].color.triplet.hex == "#ff79c6"


def test_element_complex(static_theme):
    assert static_theme.elements["text"].color.name == "#f8f8f2"
    assert static_theme.elements["text"].color.triplet.hex == "#f8f8f2"
    assert static_theme.elements["text"].bgcolor.name == "#282a36"
    assert static_theme.elements["text"].bgcolor.triplet.hex == "#282a36"
    assert static_theme.elements["text_high"].color.name == "#f8f8f2"
    assert static_theme.elements["text_high"].color.triplet.hex == "#f8f8f2"
    assert static_theme.elements["text_high"].bgcolor.name == "#282a36"
    assert static_theme.elements["text_high"].bgcolor.triplet.hex == "#282a36"


def test_elements_load_order(static_theme):
    assert not static_theme.elements["notyet"]
    assert isinstance(static_theme.elements["notyet"], rich.style.Style)


def test_element_unknown_reference(static_theme):
    assert not static_theme.elements["color2"]
    assert isinstance(static_theme.elements["color2"], rich.style.Style)


def test_element_empty(static_theme):
    assert not static_theme.elements["color3"]
    assert isinstance(static_theme.elements["color3"], rich.style.Style)
