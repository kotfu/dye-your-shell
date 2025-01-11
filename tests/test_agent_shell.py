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
# test the environment_variables agent
#
TEMPLATES = [
    ("{{styles.dark_orange|fg_hex}}", "#ff6c1c"),
    ("{{variables.greeting}}", "Hello There."),
]


@pytest.mark.parametrize("template, rendered", TEMPLATES)
def test_shell(dye_cmdline, capsys, template, rendered):
    """
    pattern_str has two kinds of embedded processing

    First, the python f-string takes the template argument
    and puts it where {template} is

    Second, jinja is going to process the whole string and pick up the
    {{ colors.background }} thing

    These tests aren't comprehensive for template rendering, but we do need
    to make sure that it renders something, because it's up to the agent
    to call the template rendering code
    """
    pattern_str = (
        """
            [colors]
            background = "#222222"

            [styles]
            dark_orange = "#ff6c1c on {{ colors.background }}"

            [variables]
            greeting = "Hello There."
            response = "General Kenobi."
        """
        f"""
            [scopes.gum]
            agent = "shell"
            command.one = "echo {template}"
            command.two = "printf {template}"
        """
    )
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, _ = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert f"echo {rendered}" in out
    assert f"printf {rendered}" in out


###
###
###
#
# test the shell agent
#
def test_shell(dye_cmdline, capsys):
    tomlstr = """
        [variables]
        greeting = "hello there"

        [styles]
        purple = "#A020F0"

        [scope.shortcut]
        agent = "shell"
        command.first = "echo {var:greeting}"
        command.next = "echo general kenobi"
        command.last = "echo {style:purple}"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == "echo hello there\necho general kenobi\necho #a020f0\n"


def test_shell_ansi(dye_cmdline, capsys):
    tomlstr = """
        [variables]
        greeting = "hello there"

        [styles]
        purple = "#A020F0"

        [scope.shortcut]
        agent = "shell"
        command.first = "echo {style:purple:ansi_on}{var:greeting}{style:purple:ansi_off}"
    """  # noqa: E501
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == "echo \x1b[38;2;160;32;240mhello there\x1b[0m\n"


def test_shell_enabled_if(dye_cmdline, capsys):
    # we have separate tests for enabled_if, but since it's super useful with the
    # shell agent, i'm including another test here
    tomlstr = """
        [scope.shortcut]
        agent = "shell"
        enabled_if = "[[ 1 == 0 ]]"
        command.first = "shortcuts run 'My Shortcut Name'"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert not out


def test_shell_multiline(dye_cmdline, capsys):
    tomlstr = """
        [scope.multiline]
        agent = "shell"
        command.long = '''
echo hello there
echo general kenobi
if [[ 1 == 1 ]]; then
  echo "yes sir"
fi
'''
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    # yes we have two line breaks at the end of what we expect
    # because there are single line commands, we have to output
    # a newline after the command
    # but on multiline commands that might give an extra newline
    # at the end of the day, that makes zero difference in
    # functionality, but it matters for testing, hence this note
    expected = """echo hello there
echo general kenobi
if [[ 1 == 1 ]]; then
  echo "yes sir"
fi

"""
    assert out == expected


def test_shell_no_commands(dye_cmdline, capsys):
    tomlstr = """
        [scope.shortcut]
        agent = "shell"
    """
    exit_code = dye_cmdline("activate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert not out
