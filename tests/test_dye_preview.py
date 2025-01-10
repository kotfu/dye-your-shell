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
# test the preview command
#
def test_preview(dye_cmdline, capsys):
    theme_toml = """
        [styles]
        # have to define a 'text' style or preview doesn't work
        text = "#f6f6f0 on #222531"
        current_line =  "#f8f8f2 on #44475a"
        comment =  "#6272a4"
    """
    exit_code = dye_cmdline("preview", theme_toml)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert out
    assert not err
    # here's a list of strings that should be in the output
    tests = ["current_line", "comment", "text"]
    for test in tests:
        assert test in out
