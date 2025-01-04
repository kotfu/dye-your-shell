#
# Copyright (c) 2023 Jared Crapo
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
import rich.errors
import rich.style

from shell_themer.parsers import StyleParser


def test_parse_text_plain():
    sp = StyleParser()
    style = sp.parse_text("#aaff00")
    assert isinstance(style, rich.style.Style)
    assert style.color.name == "#aaff00"


def test_parse_text_complex():
    sp = StyleParser()
    style = sp.parse_text("bold white on red")
    assert isinstance(style, rich.style.Style)
    assert style.bold is True
    assert style.color.name == "white"
    assert style.bgcolor.name == "red"


def test_parse_text_invalid():
    sp = StyleParser()
    with pytest.raises(rich.errors.StyleSyntaxError):
        _ = sp.parse_text("not a valid style")


def test_style_parse_dict():
    variables = {"qyellow": "#ffff00"}
    # parse up some base styles
    raw_theme = {
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "current_line": "#f8f8f2 on #44475a",
        "warning": "{var:qyellow}",
    }
    bp = StyleParser(None, variables)
    theme = bp.parse_dict(raw_theme)

    sp = StyleParser(theme, variables)
    styleobj = sp.parse_text("current_line")
    assert styleobj.color.name == "#f8f8f2"
    assert styleobj.bgcolor.name == "#44475a"
    styleobj = sp.parse_text("warning")
    assert styleobj.color.name == "#ffff00"
