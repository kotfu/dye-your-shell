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
import rich.errors
import rich.style

import dye.agents
from dye import Dye


#
# test GeneratorBase functionality
#
def test_agent_classmap():
    classmap = dye.agents.AgentBase.classmap
    assert "environment_variables" in classmap
    assert "bogusagent" not in classmap
    assert classmap["environment_variables"].__name__ == "EnvironmentVariables"


def test_agent_name():
    envgen = dye.agents.EnvironmentVariables(None, None, None)
    assert envgen.agent == "environment_variables"
    fzfgen = dye.agents.Fzf(None, None, None)
    assert fzfgen.agent == "fzf"


#
# test high level generation functions
#
def test_activate_single_scope(dye_cmdline, capsys):
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
        agent = "iterm"
        style.foreground = "foreground"
        style.background = "background"

        [scope.fzf]
        agent = "fzf"

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
    exit_code = dye_cmdline("activate -s fzf", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out
    assert not err
    assert out.count("\n") == 1


def test_activate_unknown_scope(dye_cmdline, capsys):
    tomlstr = """
        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"

        [scope.iterm]
        agent = "iterm"
        style.foreground = "foreground"
        style.background = "background"

        [scope.ls]
        # set some environment variables
        environment.unset = ["SOMEVAR", "ANOTHERVAR"]
        environment.export.LS_COLORS = "ace ventura"
    """
    exit_code = dye_cmdline("activate -s unknownscope", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert err


def test_activate_no_scopes(dye_cmdline, capsys):
    tomlstr = """
        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not out
    assert not err


#
# test elements common to all scopes
#
def test_activate_enabled(dye_cmdline, capsys):
    tomlstr = """
        [scope.nolistvar]
        enabled = false
        agent = "environment_variables"
        unset = "NOLISTVAR"

        [scope.somevar]
        enabled = true
        agent = "environment_variables"
        unset = "SOMEVAR"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert "unset SOMEVAR" in out
    assert "unset NOLISTVAR" not in out


def test_activate_enabled_false_enabled_if_ignored(dye_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        enabled = false
        enabled_if = "[[ 1 == 1 ]]"
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert not out


def test_activate_enabled_true_enabed_if_ignored(dye_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        enabled = true
        enabled_if = "[[ 0 == 1 ]]"
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert "unset NOLISTVAR" in out


def test_activate_enabled_invalid_value(dye_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        enabled = "notaboolean"
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert not out
    assert "to be true or false" in err


ENABLED_IFS = [
    ("", True),
    ("echo", True),
    ("[[ 1 == 1 ]]", True),
    ("[[ 1 == 0 ]]", False),
    ("{var:echocmd} hi", True),
    ("{variable:falsetest}", False),
]


@pytest.mark.parametrize("cmd, enabled", ENABLED_IFS)
def test_activate_enabled_if(cmd, enabled, dye_cmdline, capsys):
    tomlstr = f"""
        [variables]
        echocmd = "/bin/echo"
        falsetest = "[[ 1 == 0 ]]"

        [scope.unset]
        enabled_if = "{cmd}"
        agent = "environment_variables"
        unset = "ENVVAR"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    if enabled:
        assert "unset ENVVAR" in out
    else:
        assert not out


def test_activate_comments(dye_cmdline, capsys):
    tomlstr = """
        [scope.nolistvar]
        enabled = false
        agent = "environment_variables"
        unset = "NOLISTVAR"

        [scope.somevar]
        enabled = true
        agent = "environment_variables"
        unset = "SOMEVAR"
    """
    exit_code = dye_cmdline("activate --comment", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert "# [scope.nolistvar]" in out
    assert "# [scope.somevar]" in out
    assert "unset SOMEVAR" in out
    assert "unset NOLISTVAR" not in out


def test_unknown_agent(dye_cmdline, capsys):
    tomlstr = """
        [scope.myprog]
        agent = "mrfusion"
        unset = "SOMEVAR"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    _, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert "unknown agent" in err
    assert "mrfusion" in err


def test_no_agent(dye_cmdline, capsys):
    tomlstr = """
        [scope.myscope]
        enabled = false
    """
    exit_code = dye_cmdline("activate", tomlstr)
    _, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_ERROR
    assert "does not have an agent" in err
    assert "myscope" in err
