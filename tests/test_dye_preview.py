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


from dye import Dye

SAMPLE_THEME = """
[colors]
foreground = "#f8f8f2"
foreground_high = "foreground"
foreground_medium = "foreground"
foreground_low = "foreground"

triad.first = "#aaaaaa"
triad.second = "#bbbbbb"
triad.third = "#cccccc"

[styles]
themeonly = "{{color.foreground}} on #393b47"
foreground = "{{ color.foreground }}"
text = "#d2d2d2 on #2d2d2d"
"""

SAMPLE_PATTERN = """
description = "Oxygen is a pattern with lots of space"
type = "dark"
version = "2.0"

requires_theme = "reqtheme"
prevent_themes = true

[colors]
pattern_purple =  "#bd93f8"
pattern_yellow =  "#f1fa8b"
notyet =  "{{ colors.yellow }}"

foreground =  "#e9e9e3"
background =  "#282a36"

foreground_unknown = "{{ colors.unknown }}"

background_high = "{{ colors.background }}"
background_medium = "{{ color.background }}"
background_low = "background"
background_double1 = "{{ color.background_low }}"
background_double2 = "background_medium"

yellow = "#e2eb9c"

triad.second = "#dd2222"

tetrad.first = "#ff1111"
tetrad.second = "#ff2222"
tetrad.third = "foreground_low"
tetrad.fourth = "{{ color.pattern_purple }}"
tetrad.fifth = "{{ colors.triad.third }}"

[styles]
notyet = "{{ styles.text }}"
foreground = "{{ color.foreground }}"
text = "bold {{ colors.foreground }} on {{ colors.background }}"
text_high = "{{ styles.text }}"
text_medium = "{{ style.text }}"
text_low = "text"
text_double1 = "{{ style.text_low }}"
text_double2 = "text_medium"
text_colorref = "{{ color.foreground_medium }}"
color1 = "#ff79c6"
color2 = "{{ colors.unknown }}"
color3 = "{{ style.unknown }}"
color4 = ""

pattern_text = '#cccccc on #ffffff'
pattern_text_high = '#000000 on #ffffff'
pattern_text_low = '#999999 on #ffffff'
pattern_yellow = "{{ colors.pattern_yellow }}"

triad_sty.first = "{{ colors.triad.first }}"
triad_sty.second = "pattern_text"
triad_sty.third = "{{ style.themeonly }}"
"""


#
# test the preview command
#
def test_preview_nothing(dye_cmdline, capsys):
    # no theme, no pattern is an error
    exit_code = dye_cmdline("preview")
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "nothing to preview" in err


def test_preview(dye_cmdline, capsys):
    exit_code = dye_cmdline("preview", SAMPLE_THEME, SAMPLE_PATTERN)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out
    assert not err
    # here's a list of strings that should be in the output
    tests = [
        "foreground",
        "pattern_purple",
        "themeonly",
        "yellow",
        "triad.second",
        "tetrad.fifth",
        "triad_sty.third",
    ]
    for test in tests:
        assert test in out


def test_theme_only(dye_cmdline, capsys):
    exit_code = dye_cmdline("preview", SAMPLE_THEME)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    tests = ["foreground_high", "triad.third", "text", "themeonly", "No pattern file."]
    for test in tests:
        assert test in out
    assert not err


def test_pattern_only(dye_cmdline, capsys):
    exit_code = dye_cmdline("preview", None, SAMPLE_PATTERN)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    tests = [
        "pattern_purple",
        "triad.second",
        "text",
        "triad_sty.third",
        "No theme file.",
    ]
    for test in tests:
        assert test in out
    assert not err


def test_no_text(dye_cmdline, capsys):
    theme_toml = """
        [colors]
        background = "#282a36"
        current_line = "#44475a"

        [styles]
        current_line =  "#f8f8f2 on #44475a"
        comment =  "{{color.comment}}"
    """
    exit_code = dye_cmdline("preview", theme_toml)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "no 'text' style defined" in err


def test_empty_style(dye_cmdline, capsys):
    theme_toml = """
        [styles]
        text = "#d2d2d2 on #2d2d2d"
        empty_style = ""
    """
    exit_code = dye_cmdline("preview", theme_toml)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert "empty_style" in out
    assert not err
