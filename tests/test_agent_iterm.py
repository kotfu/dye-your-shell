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


################
################
#
# test the iterm agent
#
def test_iterm_fg_bg(dye_cmdline, capsys):
    tomlstr = """
        [styles]
        foreground = "#ffeebb"
        background = "#221122"

        [scope.iterm]
        agent = "iterm"
        style.foreground = "foreground"
        style.background = "background"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 2
    assert lines[0] == r'builtin echo -en "\e]1337;SetColors=fg=ffeebb\a"'
    assert lines[1] == r'builtin echo -en "\e]1337;SetColors=bg=221122\a"'


def test_iterm_bg(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        style.background = "#b2cacd"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 1
    assert lines[0] == r'builtin echo -en "\e]1337;SetColors=bg=b2cacd\a"'


def test_iterm_profile(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        cursor = "box"
        style.cursor = "#b2cacd"
        profile = "myprofilename"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    # we have multiple directives in this scope, but the profile directive
    # should always come out first
    assert len(lines) == 3
    assert lines[0] == r'builtin echo -en "\e]1337;SetProfile=myprofilename\a"'


def test_iterm_cursor(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        cursor = "underline"
        style.cursor = "#cab2cd"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 2
    assert lines[0] == r'builtin echo -en "\e]1337;CursorShape=2\a"'
    assert lines[1] == r'builtin echo -en "\e]1337;SetColors=curbg=cab2cd\a"'


CURSOR_SHAPES = [
    ("block", "0"),
    ("box", "0"),
    ("vertical_bar", "1"),
    ("vertical", "1"),
    ("bar", "1"),
    ("pipe", "1"),
    ("underline", "2"),
]


@pytest.mark.parametrize("name, code", CURSOR_SHAPES)
def test_iterm_cursor_shape(dye_cmdline, capsys, name, code):
    tomlstr = f"""
        [scope.iterm]
        agent = "iterm"
        cursor = "{name}"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 1
    # fr'...' lets us use f string interpolation, but the r disables
    # escape processing, just what we need for this test
    assert lines[0] == rf'builtin echo -en "\e]1337;CursorShape={code}\a"'


def test_iterm_cursor_profile(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        profile = "smoov"
        cursor = "profile"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 2
    # fr'...' lets us use f string interpolation, but the r disables
    # escape processing, just what we need for this test
    assert lines[1] == r'builtin echo -en "\e[0q"'


def test_iterm_cursor_shape_invalid(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        cursor = "ibeam"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "unknown cursor" in err


def test_item_tab_default(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        style.tab = "default"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 1
    assert lines[0] == r'builtin echo -en "\e]6;1;bg;*;default\a"'


def test_iterm_tab_color(dye_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        style.tab = "#337799"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 3
    assert lines[0] == r'builtin echo -en "\e]6;1;bg;red;brightness;51\a"'
    assert lines[1] == r'builtin echo -en "\e]6;1;bg;green;brightness;119\a"'
    assert lines[2] == r'builtin echo -en "\e]6;1;bg;blue;brightness;153\a"'
