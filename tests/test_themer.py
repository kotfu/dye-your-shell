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


def test_loads_empty(thm_base):
    thm_base.loads("")
    assert isinstance(thm_base.definition, dict)
    assert thm_base.definition == {}
    assert isinstance(thm_base.styles, dict)
    assert thm_base.styles == {}


def test_parse_styles(thm):
    assert isinstance(thm.styles, dict)
    assert isinstance(thm.styles["cyan"], rich.style.Style)
    assert thm.styles["cyan"].color.name == "#8be9fd"
    assert thm.styles["yellow"].color.name == "#f1fa8c"


def test_domain_styles(thm):
    domain = "fzf"
    styles = thm.domain_styles(domain)
    assert isinstance(styles, dict)
    assert len(styles) == 8
    assert "indicator" in styles.keys()
    assert isinstance(styles["localstyle"], rich.style.Style)
    style = styles["selected"]
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


def test_domain_elements_unknown(thm):
    domain = "unknown"
    styles = thm.domain_styles(domain)
    assert isinstance(styles, dict)
    assert styles == {}


def test_domain_attributes(thm):
    attribs = thm.domain_attributes("fzf")
    assert isinstance(attribs, dict)
    assert attribs["processor"] == "fzf"
    assert len(attribs) == 3
    with pytest.raises(KeyError):
        _ = attribs["style"]
    assert thm.definition["domain"]["fzf"]["style"]["text"] == "foreground"


def test_domain_attributes_none(thm):
    attribs = thm.domain_attributes("noattribs")
    assert isinstance(attribs, dict)
    assert attribs == {}


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
        style = thm.get_style("not a valid style")


def test_get_style_lookup(thm):
    style = thm.get_style("current_line")
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


#
# test general rendering
#
def test_generate_single_scope(thm_cmdline, capsys):
    exit_code = thm_cmdline("generate -s fzf")
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert out
    assert not err
    assert out.count("\n") == 1


def test_generate_unknown_scope(thm_cmdline, capsys):
    exit_code = thm_cmdline("generate -s unknowndomain")
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert err
