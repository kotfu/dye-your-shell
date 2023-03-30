#
# -*- coding: utf-8 -*-
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
import rich.style
import rich.errors

from shell_themer import Themer


def test_loads_empty(thm):
    thm.loads("")
    assert isinstance(thm.definition, dict)
    assert thm.definition == {}
    assert isinstance(thm.styles, dict)
    assert thm.styles == {}


#
# test style parsing
#
def test_get_style_plain(thm):
    style = thm.get_style("#aaff00")
    assert isinstance(style, rich.style.Style)
    assert style.color.name == "#aaff00"


def test_get_style_complex(thm):
    style = thm.get_style("bold white on red")
    assert isinstance(style, rich.style.Style)
    assert style.bold is True
    assert style.color.name == "white"
    assert style.bgcolor.name == "red"


def test_get_style_invalid(thm):
    with pytest.raises(rich.errors.StyleSyntaxError):
        _ = thm.get_style("not a valid style")


def test_get_style_lookup(thm):
    tomlstr = """
[styles]
background =  "#282a36"
foreground =  "#f8f8f2"
current_line =  "#f8f8f2 on #44475a"
    """
    thm.loads(tomlstr)
    style = thm.get_style("current_line")
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


def test_parse_styles(thm):
    tomlstr = """
[styles]
background =  "#282a36"
foreground =  "#f8f8f2"
current_line =  "#f8f8f2 on #44475a"
comment =  "#6272a4"
cyan =  "#8be9fd"
green =  "#50fa7b"
orange =  "#ffb86c"
pink =  "#ff79c6"
purple =  "#bd93f9"
red =  "#ff5555"
yellow =  "#f1fa8c"

[scope.ls]
# set some environment variables
environment.unset = ["SOMEVAR", "ANOTHERVAR"]
environment.export.LS_COLORS = "ace ventura"
    """
    thm.loads(tomlstr)
    assert isinstance(thm.styles, dict)
    assert isinstance(thm.styles["cyan"], rich.style.Style)
    assert thm.styles["cyan"].color.name == "#8be9fd"
    assert thm.styles["yellow"].color.name == "#f1fa8c"


def test_styles_from(thm):
    tomlstr = """
[styles]
background =  "#282a36"
foreground =  "#f8f8f2"
current_line =  "#f8f8f2 on #44475a"
comment =  "#6272a4"
cyan =  "#8be9fd"
green =  "#50fa7b"
orange =  "#ffb86c"
pink =  "#ff79c6"
purple =  "#bd93f9"
red =  "#ff5555"
yellow =  "#f1fa8c"

[scope.iterm]
generator = "iterm"
style.foreground = "foreground"
style.background = "background"

[scope.fzf]
generator = "fzf"

# attributes specific to fzf
environment_variable = "FZF_DEFAULT_OPTS"

# command line options
opt.--prompt = ">"
opt.--border = "single"
opt.--pointer = "•"
opt.--info = "hidden"
opt.--no-sort = true
opt."+i" = true

# styles
style.text = "foreground"
style.label = "green"
style.border = "orange"
style.selected = "current_line"
style.prompt = "green"
style.indicator = "cyan"
style.match = "pink"
style.localstyle = "green on black"
"""
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("fzf")
    styles = thm.styles_from(scopedef)
    assert isinstance(styles, dict)
    assert len(styles) == 8
    assert "indicator" in styles.keys()
    assert isinstance(styles["localstyle"], rich.style.Style)
    style = styles["selected"]
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


def test_styles_from_unknown(thm):
    tomlstr = """
[scope.iterm]
generator = "iterm"
style.foreground = "foreground"
style.background = "background"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("unknown")
    styles = thm.styles_from(scopedef)
    assert isinstance(styles, dict)
    assert styles == {}


#
# test scope, parsing, and validation methods
#


def test_scopedef(thm):
    tomlstr = """
[scope.iterm]
generator = "iterm"
style.foreground = "blue"
style.background = "white"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("iterm")
    assert isinstance(scopedef, dict)
    assert scopedef["generator"] == "iterm"
    assert len(scopedef) == 2
    styles = thm.styles_from(scopedef)
    assert len(styles) == 2
    assert isinstance(styles["foreground"], rich.style.Style)


def test_scopedef_notfound(thm):
    tomlstr = """
[scope.iterm]
generator = "iterm"
style.foreground = "blue"
style.background = "white"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("notfound")
    assert isinstance(scopedef, dict)
    assert scopedef == {}


# TODO test has_scope()
# TODO test is_enabled()
# TODO test _assert_bool()


#
# test high level generation functions
#
def test_generate_single_scope(thm_cmdline, capsys):
    tomlstr = """
[styles]
background =  "#282a36"
foreground =  "#f8f8f2"
current_line =  "#f8f8f2 on #44475a"
comment =  "#6272a4"
cyan =  "#8be9fd"
green =  "#50fa7b"
orange =  "#ffb86c"
pink =  "#ff79c6"
purple =  "#bd93f9"
red =  "#ff5555"
yellow =  "#f1fa8c"

[scope.iterm]
generator = "iterm"
style.foreground = "foreground"
style.background = "background"

[scope.fzf]
generator = "fzf"

# attributes specific to fzf
environment_variable = "FZF_DEFAULT_OPTS"

# command line options
opt.--prompt = ">"
opt.--border = "single"
opt.--pointer = "•"
opt.--info = "hidden"
opt.--no-sort = true
opt."+i" = true

# styles
style.text = "foreground"
style.label = "green"
style.border = "orange"
style.selected = "current_line"
style.prompt = "green"
style.indicator = "cyan"
style.match = "pink"
style.localstyle = "green on black"
    """
    exit_code = thm_cmdline("generate -s fzf", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert out
    assert not err
    assert out.count("\n") == 1


def test_generate_unknown_scope(thm_cmdline, capsys):
    tomlstr = """
[styles]
background =  "#282a36"
foreground =  "#f8f8f2"

[scope.iterm]
generator = "iterm"
style.foreground = "foreground"
style.background = "background"

[scope.ls]
# set some environment variables
environment.unset = ["SOMEVAR", "ANOTHERVAR"]
environment.export.LS_COLORS = "ace ventura"
    """
    exit_code = thm_cmdline("generate -s unknownscope", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert err
