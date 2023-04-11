#
# -*- coding: utf-8 -*-
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

from shell_themer import Themer


#
# test the preview command
#
def test_preview(thm_cmdline, capsys):
    tomlstr = """
        [styles]
        # we intentionally don't define a "text" style, or a
        # "foreground" or a "background" style just
        # to make sure the preview works without it
        current_line =  "#f8f8f2 on #44475a"
        comment =  "#6272a4"

        [scope.iterm]
        generator = "iterm"
        style.foreground = "foreground"
        style.background = "background"

        [scope.fzf]
        generator = "fzf"
        environment_variable = "FZF_DEFAULT_OPTS"
        style.text = "foreground"

        [scope.someprog]
        environment.unset = "SOMEPROG"
    """
    exit_code = thm_cmdline("preview", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert out
    assert not err
    # here's a list of strings that should be in the output
    tests = ["current_line", "comment", "iterm", "fzf", "someprog"]
    for test in tests:
        assert test in out
