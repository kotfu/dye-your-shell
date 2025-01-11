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

from dye import Dye


#
# test the iterm agent
#
def test_profile(dye_cmdline, capsys):
    profile = "supersuper"
    pattern_str = f"""
    [scopes.iterm]
    agent = "iterm"
    profile = "{profile}"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert f"SetProfile={profile}" in out


def test_tab(dye_cmdline, capsys):
    pattern_str = """
    [scopes.iterm]
    agent = "iterm"
    styles.tab = "#ff0088"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    # Changing the tab or window title bar color actually sends
    # 3 escape sequences, one for each color value in rgb.
    # These come out as as 3 echo commands.
    assert out.count("\n") == 3
    assert "red" in out
    assert "green" in out
    assert "blue" in out


def test_tab_default(dye_cmdline, capsys):
    pattern_str = """
    [scopes.iterm]
    agent = "iterm"
    styles.tab = "default"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out.count("\n") == 1
    assert "default" in out


def test_foreground(dye_cmdline, capsys):
    pattern_str = """
    [scopes.iterm]
    agent = "iterm"
    styles.foreground = "#ff00ff"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out.count("\n") == 1
    assert "SetColors=fg=" in out


def test_background(dye_cmdline, capsys):
    pattern_str = """
    [scopes.iterm]
    agent = "iterm"
    styles.background = "#333333"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out.count("\n") == 1
    assert "SetColors=bg=" in out


CURSORS = [
    ("block", "0"),
    ("box", "0"),
    ("vertical_bar", "1"),
    ("vertical", "1"),
    ("bar", "1"),
    ("pipe", "1"),
    ("underline", "2"),
]


@pytest.mark.parametrize("name, value", CURSORS)
def test_cursor_shape(dye_cmdline, capsys, name, value):
    pattern_str = f"""
    [scopes.iterm]
    agent = "iterm"
    cursor = "{name}"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out.count("\n") == 1
    assert f"CursorShape={value}" in out


def test_cursor_profile(dye_cmdline, capsys):
    pattern_str = """
    [scopes.iterm]
    agent = "iterm"
    cursor = "profile"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out.count("\n") == 1
    assert r"\e[0q" in out


def test_cursor_style(dye_cmdline, capsys):
    pink = "df769b"
    pattern_str = f"""
    [scopes.iterm]
    agent = "iterm"
    styles.cursor = "#{pink}"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out.count("\n") == 1
    assert f"SetColors=curbg={pink}" in out
