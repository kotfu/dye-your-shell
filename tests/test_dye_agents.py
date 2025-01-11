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

from dye import Dye


#
# test the agents command (which shows the list of available agents)
#
def test_agents(dye_cmdline, capsys):
    exit_code = dye_cmdline("agents")
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    expected_agents = [
        "environment_variables",
        "eza",
        "fzf",
        "iterm",
        "gnu_ls",
        "shell",
    ]
    for agent in expected_agents:
        assert agent in out
    # the agents command outputs a rich table with a header row and a line
    # under the header
    lines = out.splitlines()
    # this is the header row
    assert "Agent" in lines[0]
    # +2 for the header line and the horizontal bar under the header line
    assert len(lines) == len(expected_agents) + 2
