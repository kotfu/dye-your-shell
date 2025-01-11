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
    ("{{variables.someopts}}", "--option=fred -v"),
    ("{{styles.dark_orange|fg_hex}}", "#ff6c1c"),
]


@pytest.mark.parametrize("template, rendered", TEMPLATES)
def test_export(dye_cmdline, capsys, template, rendered):
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
            someopts = "--option=fred -v"
        """
        f"""
            [scopes.gum]
            agent = "environment_variables"
            export.GUM_OPTS = " --cursor-foreground={template}"
            export.FRED = "{template}"
        """
    )
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert lines[0] == f'export GUM_OPTS=" --cursor-foreground={rendered}"'
    assert lines[1] == f'export FRED="{rendered}"'


def test_unset_list(dye_cmdline, capsys):
    pattern_str = """
        [variables]
        thevar = "ANOTHERVAR"

        [scopes.ls]
        agent = "environment_variables"
        unset = ["SOMEVAR", "{{ variables.thevar }}"]
        export.LS_COLORS = "ace ventura"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert lines[0] == "unset SOMEVAR"
    assert lines[1] == "unset ANOTHERVAR"
    assert lines[2] == 'export LS_COLORS="ace ventura"'


def test_unset_string(dye_cmdline, capsys):
    pattern_str = """
        [scopes.unset]
        agent = "environment_variables"
        unset = "NOLISTVAR"
    """
    exit_code = dye_cmdline("apply", None, pattern_str)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert lines[0] == "unset NOLISTVAR"
