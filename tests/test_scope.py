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


# # TODO this should test the init in GeneratorBase which sets scope_styles
# # def test_styles_from(thm):
# #     tomlstr = """
# #         [styles]
# #         background =  "#282a36"
# #         foreground =  "#f8f8f2"
# #         current_line =  "#f8f8f2 on #44475a"
# #         comment =  "#6272a4"
# #         cyan =  "#8be9fd"
# #         green =  "#50fa7b"
# #         orange =  "#ffb86c"
# #         pink =  "#ff79c6"
# #         purple =  "#bd93f9"
# #         red =  "#ff5555"
# #         yellow =  "#f1fa8c"

# #         [scope.iterm]
# #         generator = "iterm"
# #         style.foreground = "foreground"
# #         style.background = "background"

# #         [scope.fzf]
# #         generator = "fzf"

# #         # attributes specific to fzf
# #         environment_variable = "FZF_DEFAULT_OPTS"

# #         # command line options
# #         opt.--prompt = ">"
# #         opt.--border = "single"
# #         opt.--pointer = "•"
# #         opt.--info = "hidden"
# #         opt.--no-sort = true
# #         opt."+i" = true

# #         # styles
# #         style.text = "foreground"
# #         style.label = "green"
# #         style.border = "orange"
# #         style.selected = "current_line"
# #         style.prompt = "green"
# #         style.indicator = "cyan"
# #         style.match = "pink"
# #         style.localstyle = "green on black"
# #     """
# #     thm.loads(tomlstr)
# #     scopedef = thm.scopedef_for("fzf")
# #     styles = thm.styles_from(scopedef)
# #     assert isinstance(styles, dict)
# #     assert len(styles) == 8
# #     assert "indicator" in styles.keys()
# #     assert isinstance(styles["localstyle"], rich.style.Style)
# #     style = styles["selected"]
# #     assert style.color.name == "#f8f8f2"
# #     assert style.bgcolor.name == "#44475a"


# # TODO I don't think we need to test this, as long as we test the
# # init() method of GeneratorBase
# # def test_styles_from_unknown(thm):
# #     tomlstr = """
# #         [scope.iterm]
# #         generator = "iterm"
# #         style.foreground = "foreground"
# #         style.background = "background"
# #     """
# #     thm.loads(tomlstr)
# #     scopedef = thm.scopedef_for("unknown")
# #     styles = thm.styles_from(scopedef)
# #     assert isinstance(styles, dict)
# #     assert styles == {}
