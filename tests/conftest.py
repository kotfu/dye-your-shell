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

import pytest

from shell_themer import Themer


@pytest.fixture
def thm():
    thm = Themer(prog="shell-themer")
    return thm


@pytest.fixture
def thm_cmdline(thm, mocker):
    # defining a fixture that returns a function
    # allows us to call the fixture and pass parameters to it
    # ie:
    #
    # def test_generate_environment_unset_list(thm_cmdline, capsys):
    #     tomlstr = """
    #     [scope.ls]
    #     # set some environment variables
    #     environment.unset = ["SOMEVAR", "ANOTHERVAR"]
    #     environment.export.LS_COLORS = "ace ventura"
    #     """
    #     exit_code = thm_cmdline("generate", tomlstr)
    #     ...

    def _executor(cmdline, toml=None):
        if isinstance(cmdline, str):
            argv = cmdline.split(" ")
        elif isinstance(cmdline, list):
            argv = cmdline
        else:
            argv = []
        try:
            args = thm.argparser().parse_args(argv)
        except SystemExit as err:
            return err.code
        if toml:
            thm.loads(toml)
        # monkeypatch load_from_args() because that won't work so well
        mocker.patch("shell_themer.Themer.load_from_args", autospec=True)
        return thm.dispatch(args)

    return _executor
