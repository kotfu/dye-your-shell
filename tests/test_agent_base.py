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

import dye
from dye import Pattern


#
# test AgentBase
#
def test_agent_base_classmap():
    classmap = dye.agents.AgentBase.classmap
    assert "environment_variables" in classmap
    assert "bogusagent" not in classmap
    assert classmap["environment_variables"].__name__ == "EnvironmentVariables"


def test_agent_base_name():
    # we have to have a pattern in order for the agent to initialize
    # so lets make a fake one
    pattern_str = """
    [scopes.myscope]
    agent = "shell"
    """
    pattern = Pattern.loads(pattern_str)
    pattern.process()
    eza = dye.agents.EnvironmentVariables("myscope", pattern)
    assert eza.agent == "environment_variables"
    fzfgen = dye.agents.Fzf("myscope", pattern)
    assert fzfgen.agent == "fzf"
