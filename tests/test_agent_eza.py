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

import dye
from dye import Dye, Pattern

#
# test the eza agent
#

# we only reallly have to test that the style name maps to the right code
# ie directory -> di, or setuid -> su. The ansi codes are created by rich.style
# so we don't really need to test much of that
STYLE_TO_EZACOLORS = [
    ("filekinds:normal", "default", "fi=0"),
    ("filekinds:directory", "#8be9fd", "di=38;2;139;233;253"),
    ("filekinds:symlink", "green4 bold", "ln=1;38;5;28"),
    ("lc", "blue on white", "lc=34;47"),
    ("pi", "#f8f8f2 on #44475a underline", "pi=4;38;2;248;248;242;48;2;68;71;90"),
    ("filekinds:socket", "bright_white", "so=97"),
    ("filekinds:block_device", "default", "bd=0"),
    ("filekinds:char_device", "black", "cd=30"),
    ("broken_symlink", "bright_blue", "or=94"),
    ("perms:special_user_file", "bright_blue", "su=94"),
    ("perms:special_other", "bright_red", "sf=91"),
    ("perms:other_write", "deep_pink2 on #ffffaf", "tw=38;5;197;48;2;255;255;175"),
    ("filekinds:executable", "cornflower_blue on grey82", "ex=38;5;69;48;5;252"),
    ("size:number_style", "#7060eb", "sn=38;2;112;96;235"),
    ("*.toml", "#8be9fd", "*.toml=38;2;139;233;253"),
]


@pytest.mark.parametrize("name, styledef, expected", STYLE_TO_EZACOLORS)
def test_eza_colors_from_style(name, styledef, expected):
    style = rich.style.Style.parse(styledef)
    # we have to have a pattern in order for the agent to initialize
    # so lets make a fake one
    pattern_str = """
    [scopes.myscope]
    agent = "eza"
    """
    pattern = Pattern.loads(pattern_str)
    pattern.process()
    agent = dye.agents.Eza("myscope", pattern)
    code, render = agent.ls_colors_from_style(
        name,
        style,
        agent.EZA_COLORS_MAP,
        "myscope",
        allow_unknown=True,
    )
    assert render == expected
    assert code == expected.split("=", 1)[0]


def test_eza_colors_no_styles(dye_cmdline, capsys):
    pattern_str = """
        [scopes.eza]
        agent = "eza"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == 'export EZA_COLORS=""\n'


def test_eza_colors_environment_variable(dye_cmdline, capsys):
    pattern_str = """
        [scopes.eza]
        agent = "eza"
        environment_variable = "OTHER_EZA_COLOR"
        styles.'filekinds:normal' = "default"
        styles.'size:number_style' = "#7060eb"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == 'export OTHER_EZA_COLOR="fi=0:sn=38;2;112;96;235"\n'


def test_eza_colors_clear_builtin(dye_cmdline, capsys):
    pattern_str = """
        [scopes.e]
        agent = "eza"
        clear_builtin = true
        styles.'filekinds:directory' = "bright_blue"
        styles.uu = "bright_red"
        styles.punctuation = "#555555"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    expected = 'export EZA_COLORS="reset:di=94:uu=91:xx=38;2;85;85;85"\n'
    assert out == expected


def test_eza_colors_clear_builtin_not_boolean(dye_cmdline, capsys):
    pattern_str = """
        [scopes.ec]
        agent = "eza"
        clear_builtin = "error"
        styles.directory = "bright_blue"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "'clear_builtin' to be true or false" in err
