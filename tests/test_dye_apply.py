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

from dye import Dye

#
# test scope selection
#
SCOPE_PATTERN = """
    [colors]
    background =  "#282a36"
    foreground =  "#f8f8f2"

    [styles]
    current_line =  "#f8f8f2 on #44475a"
    comment =  "#6272a4"
    cyan =  "#8be9fd"
    green =  "#50fa7b"
    orange =  "#ffb86c"
    pink =  "#ff79c6"
    purple =  "#bd93f9"
    red =  "#ff5555"
    yellow =  "#f1fa8c"

    [scopes.iterm]
    agent = "iterm"
    styles.foreground = "{{colors.foreground}}"
    styles.background = "{{colors.background}}"

    [scopes.fzf]
    agent = "fzf"
    environment_variable = "FZF_DEFAULT_OPTS"

    opt.--prompt = ">"
    opt.--border = "single"
    opt.--pointer = "•"
    opt.--info = "hidden"
    opt.--no-sort = true
    opt."+i" = true

    styles.text = "{{colors.foreground}}"
    styles.label = "{{styles.green}}"
    styles.border = "{{styles.orange}}"
    styles.selected = "{{styles.current_line}}"
    styles.prompt = "{{styles.green}}"
    styles.indicator = "{{styles.cyan}}"
    styles.match = "{{styles.pink}}"
    """


def test_single_scope(dye_cmdline, capsys):
    exit_code = dye_cmdline("apply -s fzf", None, SCOPE_PATTERN)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out
    assert not err
    lines = out.splitlines()
    assert len(lines) == 1


def test_all_scopes(dye_cmdline, capsys):
    exit_code = dye_cmdline("apply", None, SCOPE_PATTERN)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out
    assert not err
    lines = out.splitlines()
    # 2 lines from iterm, 1 from fzf
    assert len(lines) == 3


def test_unknown_scope(dye_cmdline, capsys):
    exit_code = dye_cmdline("apply -s unknownscope", None, SCOPE_PATTERN)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert err


def test_no_scopes(dye_cmdline, capsys):
    pattern_str = """
        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not out
    assert not err


#
# make sure scopes have an agent
#
def test_unknown_agent(dye_cmdline, capsys):
    pattern_str = """
        [scopes.myprog]
        agent = "mrfusion"
        something = "idunno"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "unknown agent" in err
    assert "mrfusion" in err


def test_no_agent(dye_cmdline, capsys):
    pattern_str = """
        [scopes.myscope]
        enabled = false
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "does not have an agent" in err
    assert "myscope" in err


#
# test enabled
#
def test_enabled(dye_cmdline, capsys):
    pattern_str = """
        [scopes.one]
        enabled = false
        agent = "environment_variables"
        unset = "NOLISTVAR"

        [scopes.two]
        enabled = true
        agent = "environment_variables"
        unset = "SOMEVAR"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert "unset SOMEVAR" in out
    assert "unset NOLISTVAR" not in out


def test_enabled_false_enabled_if_ignored(dye_cmdline, capsys):
    pattern_str = """
        [scopes.unset]
        enabled = false
        enabled_if = "[[ 1 == 1 ]]"
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert not out


def test_enabled_true_enabed_if_ignored(dye_cmdline, capsys):
    pattern_str = """
        [scopes.unset]
        enabled = true
        enabled_if = "[[ 0 == 1 ]]"
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert "unset NOLISTVAR" in out


def test_enabled_invalid_value(dye_cmdline, capsys):
    pattern_str = """
        [scopes.unset]
        enabled = "notaboolean"
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "to be true or false" in err


ENABLED_IFS = [
    ("", True),
    ("echo", True),
    ("[[ 1 == 1 ]]", True),
    ("[[ 1 == 0 ]]", False),
    ("{{variables.echocmd}} hi", True),
    ("{{variables.falsetest}}", False),
]


@pytest.mark.parametrize("cmd, enabled", ENABLED_IFS)
def test_activate_enabled_if(cmd, enabled, dye_cmdline, capsys):
    pattern_str = f"""
        [variables]
        echocmd = "builtin echo"
        falsetest = "[[ 1 == 0 ]]"

        [scopes.unset]
        enabled_if = "{cmd}"
        agent = "environment_variables"
        unset = "ENVVAR"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    if enabled:
        assert "unset ENVVAR" in out
    else:
        assert not out


#
# test comments
#
def test_comments(dye_cmdline, capsys):
    pattern_str = """
        [scopes.nolistvar]
        enabled = false
        agent = "environment_variables"
        unset = "NOLISTVAR"

        [scopes.somevar]
        enabled = true
        agent = "environment_variables"
        unset = "SOMEVAR"
    """
    exit_code = dye_cmdline("apply --comment", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    # there is a long message on skipped
    assert "# scope 'nolistvar' skipped" in out
    assert "# scope 'somevar'" in lines
    assert "unset SOMEVAR" in lines
    assert "unset NOLISTVAR" not in lines
