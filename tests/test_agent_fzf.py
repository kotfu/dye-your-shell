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
# test the fzf agent
#
ATTRIBS_TO_FZF = [
    ("bold", "regular:bold"),
    ("underline", "regular:underline"),
    ("reverse", "regular:reverse"),
    ("dim", "regular:dim"),
    ("italic", "regular:italic"),
    ("strike", "regular:strikethrough"),
    ("bold underline", "regular:bold:underline"),
    ("underline italic", "regular:underline:italic"),
    ("italic underline", "regular:underline:italic"),
]


@pytest.mark.parametrize("styledef, fzf", ATTRIBS_TO_FZF)
def test_fzf_attribs_from_style(styledef, fzf):
    style = rich.style.Style.parse(styledef)
    genny = dye.agents.Fzf(None, None, None, None, None)
    assert fzf == genny._fzf_attribs_from_style(style)


STYLE_TO_FZF = [
    # text, current-line, selected-line and preview styles have special processing
    # for foreground and background colors
    ("text", "", ""),
    ("text", "default", "fg:-1:regular"),
    ("text", "default on default", "fg:-1:regular,bg:-1"),
    ("text", "bold default on default underline", "fg:-1:regular:bold:underline,bg:-1"),
    ("text", "white on bright_red", "fg:7:regular,bg:9"),
    ("text", "bright_white", "fg:15:regular"),
    ("text", "bright_yellow on color(4)", "fg:11:regular,bg:4"),
    ("text", "green4", "fg:28:regular"),
    ("current-line", "navy_blue dim on grey82", "fg+:17:regular:dim,bg+:252"),
    (
        "selected-line",
        "navy_blue dim on grey82",
        "selected-fg:17:regular:dim,selected-bg:252",
    ),
    ("preview", "#af00ff on bright_white", "preview-fg:#af00ff:regular,preview-bg:15"),
    # other styles do not
    ("border", "magenta", "border:5:regular"),
    ("query", "#2932dc", "query:#2932dc:regular"),
]


@pytest.mark.parametrize("name, styledef, fzf", STYLE_TO_FZF)
def test_fzf_from_style(name, styledef, fzf):
    style = rich.style.Style.parse(styledef)
    genny = dye.agents.Fzf(None, None, None, None, None)
    assert fzf == genny._fzf_from_style(name, style)


def test_fzf(dye_cmdline, capsys):
    tomlstr = """
        [styles]
        purple = "#7060eb"

        [variables]
        bstyle = "rounded"

        [scope.fzf]
        agent = "fzf"
        environment_variable = "QQQ"
        opt."+i" = true
        opt.--border = "{var:bstyle}"
        style.prompt = "magenta3"
        style.info = "purple"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    expected = (
        """export QQQ=" +i --border='rounded'"""
        """ --color='prompt:164:regular,info:#7060eb:regular'"\n"""
    )
    assert out == expected


def test_fzf_no_opts(dye_cmdline, capsys):
    tomlstr = """
        [variables]
        varname = "ZZ"

        [scope.fzf]
        agent = "fzf"
        environment_variable = "Q{var:varname}QQ"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == """export QZZQQ=""\n"""


def test_fzf_no_varname(dye_cmdline, capsys):
    tomlstr = """
        [scope.fzf]
        agent = "fzf"
        opt."+i" = true
        opt.--border = "rounded"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert "FZF_DEFAULT_OPTS" in out
