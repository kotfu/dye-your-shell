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
# test the gnu_ls agent
#

# we only reallly have to test that the style name maps to the right code in ls_colors
# ie directory -> di, or setuid -> su. The ansi codes are created by rich.style
# so we don't really need to test much of that
STYLE_TO_LSCOLORS = [
    ("text", "", ""),
    ("text", "default", "no=0"),
    ("file", "default", "fi=0"),
    ("directory", "#8be9fd", "di=38;2;139;233;253"),
    ("symlink", "green4 bold", "ln=1;38;5;28"),
    ("multi_hard_link", "blue on white", "mh=34;47"),
    ("pipe", "#f8f8f2 on #44475a underline", "pi=4;38;2;248;248;242;48;2;68;71;90"),
    ("so", "bright_white", "so=97"),
    ("door", "bright_white", "do=97"),
    ("block_device", "default", "bd=0"),
    ("character_device", "black", "cd=30"),
    ("broken_symlink", "bright_blue", "or=94"),
    ("missing_symlink_target", "bright_blue", "mi=94"),
    ("setuid", "bright_blue", "su=94"),
    ("setgid", "bright_red", "sg=91"),
    ("sticky", "blue_violet", "st=38;5;57"),
    ("other_writable", "blue_violet italic", "ow=3;38;5;57"),
    ("sticky_other_writable", "deep_pink2 on #ffffaf", "tw=38;5;197;48;2;255;255;175"),
    ("executable_file", "cornflower_blue on grey82", "ex=38;5;69;48;5;252"),
    ("file_with_capability", "red on black", "ca=31;40"),
]


@pytest.mark.parametrize("name, styledef, expected", STYLE_TO_LSCOLORS)
def test_ls_colors_from_style(name, styledef, expected):
    style = rich.style.Style.parse(styledef)
    # we have to have a pattern in order for the agent to initialize
    # so lets make a fake one
    pattern_str = """
    [scopes.myscope]
    agent = "gnu_ls"
    """
    pattern = Pattern.loads(pattern_str)
    pattern.process()
    agent = dye.agents.GnuLs("myscope", pattern)
    # now we can go test the render
    code, render = agent.ls_colors_from_style(
        name,
        style,
        agent.LS_COLORS_MAP,
        "myscope",
        allow_unknown=False,
    )
    assert render == expected
    assert code == expected[0:2]


def test_ls_colors_no_styles(dye_cmdline, capsys):
    pattern_str = """
        [scopes.lsc]
        agent = "gnu_ls"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == 'export LS_COLORS=""\n'


def test_ls_colors_unknown_style(dye_cmdline, capsys):
    pattern_str = """
        [scopes.lsc]
        agent = "gnu_ls"
        styles.bundleid = "default"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert "unknown style" in err
    assert "lsc" in err


def test_ls_colors_environment_variable(dye_cmdline, capsys):
    pattern_str = """
        [scopes.lsc]
        agent = "gnu_ls"
        environment_variable = "OTHER_LS_COLOR"
        styles.file = "default"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == 'export OTHER_LS_COLOR="fi=0"\n'


def test_ls_colors_styles_variables(dye_cmdline, capsys):
    pattern_str = """
        [variables]
        pinkvar = "magenta3"

        [styles]
        warning = "yellow on red"

        [scopes.lsc]
        agent = "gnu_ls"
        styles.file = "{{styles.warning}}"
        styles.directory = "{{variables.pinkvar}}"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == 'export LS_COLORS="fi=33;41:di=38;5;164"\n'


def test_ls_colors_clear_builtin(dye_cmdline, capsys):
    pattern_str = """
        [scopes.lsc]
        agent = "gnu_ls"
        clear_builtin = true
        styles.directory = "bright_blue"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    expected = (
        'export LS_COLORS="di=94:no=0:fi=0:ln=0:'
        "mh=0:pi=0:so=0:do=0:bd=0:cd=0:or=0:mi=0:"
        'su=0:sg=0:st=0:ow=0:tw=0:ex=0:ca=0"\n'
    )
    assert out == expected


def test_ls_colors_clear_builtin_not_boolean(dye_cmdline, capsys):
    pattern_str = """
        [scopes.lsc]
        agent = "gnu_ls"
        clear_builtin = "error"
        style.directory = "bright_blue"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "'clear_builtin' to be true or false" in err
