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
import rich

from dye import Dye, Pattern, Theme


@pytest.fixture
def dye_cmdline(mocker):
    '''a fixture that simulates runing dye from the command line

    this fixture returns a function, which allows us to call
    the fixture and pass parameters to it

    def test_unset_list(dye_cmdline, capsys):
        theme = """
        [styles]
        text = "#dddddd on #222222
        """
        pattern = """
        [scope.ls]
        agent = "environment_variables"
        # set some environment variables
        unset = ["SOMEVAR", "ANOTHERVAR"]
        export.LS_COLORS = "ace ventura"
        """
        exit_code = dye_cmdline("apply -c", styles, pattern)
        ...

    This fixture allows us to pass a theme and a pattern in as strings,
    and also pass in any 'dye' command line we want. The fixture then
    patches the styles and pattern into 'dye' and runs the command line.

    Very convenient.
    '''
    # patch up the console objects so we get ansi output and don't wrap text
    console_patch = mocker.patch("dye.Dye._create_console")
    console_patch.return_value = rich.console.Console(
        soft_wrap=True,
        markup=False,
        emoji=False,
        highlight=False,
        # force display to true color so we can look for ansi codes in output
        color_system="truecolor",
        # don't let it autodetect the width, we don't want any line wrapping
        width=2048,
    )

    error_console_patch = mocker.patch("dye.Dye._create_error_console")
    error_console_patch.return_value = rich.console.Console(
        stderr=True,
        soft_wrap=True,
        markup=False,
        emoji=False,
        highlight=False,
        # force display to true color so we can look for ansi codes in output
        color_system="truecolor",
        # don't let it autodetect the width, we don't want any line wrapping
        width=2048,
    )

    dye = Dye()

    def _executor(cmdline, theme_toml=None, pattern_toml=None):
        if isinstance(cmdline, str):
            argv = cmdline.split(" ")
        elif isinstance(cmdline, list):
            argv = cmdline
        else:
            argv = []
        try:
            args = dye.argparser().parse_args(argv)
        except SystemExit as err:
            return err.code

        # create theme and pattern objects from the toml we were given
        theme = Theme.loads(theme_toml)
        pattern = Pattern.loads(pattern_toml)
        pattern.process()

        # patch Dye methods to return our objects
        theme_patch = mocker.patch("dye.Dye.load_theme_from_args")
        theme_patch.return_value = theme
        pattern_patch = mocker.patch("dye.Dye.load_pattern_from_args")
        pattern_patch.return_value = pattern

        # now go run the command
        return dye.dispatch("dye", args)

    return _executor
