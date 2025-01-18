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

from dye.exceptions import DyeError
from dye.pattern import Pattern
from dye.scope import Scope

SAMPLE_PATTERN = """
[styles]
orange = "#d5971a"
cyan = "#09ecff"
purple = "#7060eb"

triad.first = "purple"
triad.second = "cyan"
triad.third = "orange"

[scopes.iterm]
agent = "iterm"
cursor = "block"

[scopes.nocolor]
agent = "environment_variables"
export.NO_COLOR = "true"

[scopes.shell]
agent = "shell"
is_enabled = false
command.dontrun = "echo qqq"

[scopes.fzf]
agent = "fzf"
styles.file = "orange"
styles.directory = "{{ style.cyan }}"
style.border = "purple"
# purple should win
styles.prompt = "purple"
style.prompt = "orange"

[scopes.fzf2]
agent = "fzf"
environment_variable = "MY_SPECIAL_FZF_OPTS"
style.file = "triad.first"
style.directory = "{{ style.triad.second }}"
styles.prompt = "{{ styles.triad.third }}"
"""


@pytest.fixture
def spat():
    pattern = Pattern.loads(SAMPLE_PATTERN)
    return pattern


def test_init_scope_not_found(spat):
    with pytest.raises(DyeError):
        Scope("scopedoesntexist", spat)


def test_scope_no_agent():
    pattern_str = """
    [scopes.noagent]
    """
    with pytest.raises(DyeError):
        Pattern.loads(pattern_str)


def test_scope_unknown_agent():
    pattern_str = """
    [scopes.unknown]
    agent = "fredflintstone"
    """
    with pytest.raises(DyeError):
        Pattern.loads(pattern_str)


def test_scope_styles_lookup(spat):
    scope = spat.scopes["fzf"]
    assert scope.styles["file"] == spat.styles["orange"]
    assert scope.styles["directory"] == spat.styles["cyan"]


def test_scope_style(spat):
    # check that you can use
    # style.file = "#ffffff" and it will work just like styles.file = "#ffffff" does
    scope = spat.scopes["fzf"]
    assert scope.styles["border"] == spat.styles["purple"]


def test_scope_styles_overrides_style(spat):
    # check that if you have both
    # styles.prompt = "#333333"
    # style.prompt = "#ffffff"
    # you get #333333
    scope = spat.scopes["fzf"]
    assert scope.styles["prompt"] == spat.styles["purple"]


def test_scope_styles_subtable1(spat):
    scope = spat.scopes["fzf2"]
    assert scope.styles["file"] == spat.styles["purple"]


def test_scope_styles_subtable2(spat):
    scope = spat.scopes["fzf2"]
    assert scope.styles["directory"] == spat.styles["cyan"]


def test_scope_styles_subtable3(spat):
    scope = spat.scopes["fzf2"]
    assert scope.styles["prompt"] == spat.styles["orange"]
