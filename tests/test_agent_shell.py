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

from dye import Dye


#
# test the shell agent
#
def test_shell(dye_cmdline, capsys):
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
    pattern_str = """
            [colors]
            background = "#222222"

            [styles]
            dark_orange = "#ff6c1c on {{ colors.background }}"

            [variables]
            greeting = "Hello There."
            response = "General Kenobi."

            [scopes.obi-wan]
            agent = "shell"
            command.first = "echo {{variables.greeting}}"
            command.next = "printf {{variables.response}}"
            command.last = "echo {{styles.dark_orange|bg_hex}}"
        """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert out == "echo Hello There.\nprintf General Kenobi.\necho #222222\n"


def test_shell_multiline(dye_cmdline, capsys):
    pattern_str = """
        [variables]
        greeting = "hello there"

        [scopes.multiline]
        agent = "shell"
        command.long = '''
echo {{variables.greeting}}
echo general kenobi
if [[ 1 == 1 ]]; then
  echo "yes sir"
fi
'''
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    expected = """echo hello there
echo general kenobi
if [[ 1 == 1 ]]; then
  echo "yes sir"
fi
"""
    assert out == expected


def test_shell_no_commands(dye_cmdline, capsys):
    pattern_str = """
        [scopes.noop]
        agent = "shell"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    assert not out
