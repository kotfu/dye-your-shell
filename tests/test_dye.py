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

import os

import pytest
from rich_argparse import RichHelpFormatter

from dye import Dye
from dye import __main__ as mainmodule


#
# test output color logic
#
def test_output_color_cmdline(dye_cmdline, mocker):
    # command line color arguments should override
    # all environment variables
    RichHelpFormatter.styles["argparse.text"] = "#000000"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"SHELL_THEMER_COLORS": "text=#f0f0f0"})
    mocker.patch.dict(os.environ, {"NO_COLOR": "doesn't matter"})
    argv = [
        "--help",
        "--color=text=#ffff00:args=#bd93f9:metavar=#f8f8f2 on #44475a bold",
    ]
    dye_cmdline(argv)
    assert RichHelpFormatter.styles["argparse.text"] == "#ffff00"
    assert RichHelpFormatter.styles["argparse.args"] == "#bd93f9"
    assert RichHelpFormatter.styles["argparse.metavar"] == "#f8f8f2 on #44475a bold"


def test_output_color_no_color(dye_cmdline, mocker):
    mocker.patch.dict(os.environ, {}, clear=True)
    RichHelpFormatter.styles["argparse.text"] = "#ff00ff"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"NO_COLOR": "doesn't matter"})
    dye_cmdline("--help")
    for element in Dye.HELP_ELEMENTS:
        assert RichHelpFormatter.styles[f"argparse.{element}"] == "default"


def test_output_color_envs_only(dye_cmdline, mocker):
    # NO_COLOR should override SHELL_THEMER_COLORS
    RichHelpFormatter.styles["argparse.text"] = "#333333"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"DYE_COLORS": "text=#f0f0f0"})
    mocker.patch.dict(os.environ, {"NO_COLOR": "doesn't matter"})
    dye_cmdline("--help")
    for element in Dye.HELP_ELEMENTS:
        assert RichHelpFormatter.styles[f"argparse.{element}"] == "default"


def test_output_color_env_color(dye_cmdline, mocker):
    # SHELL_THEMER_COLORS should override default colors
    RichHelpFormatter.styles["argparse.text"] = "#333333"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"DYE_COLORS": "text=#f0f0f0"})
    dye_cmdline("--help")
    assert RichHelpFormatter.styles["argparse.text"] == "#f0f0f0"


def test_output_color_env_empty(dye_cmdline, mocker):
    # SHELL_THEMER_COLORS should override default colors
    RichHelpFormatter.styles["argparse.text"] = "#ff00ff"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"DYE_COLORS": ""})
    dye_cmdline("--help")
    assert RichHelpFormatter.styles["argparse.text"] == "default"


#
# test unknown commands, no commands, help, and version
#
def test_help_option(dye_cmdline, capsys):
    exit_code = dye_cmdline("--help")
    assert exit_code == Dye.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "preview" in out
    assert "--no-color" in out


def test_h_option(dye_cmdline, capsys):
    exit_code = dye_cmdline("-h")
    assert exit_code == Dye.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "preview" in out
    assert "--no-color" in out


def test_version_option(dye_cmdline, capsys):
    exit_code = dye_cmdline("--version")
    assert exit_code == Dye.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "dye" in out


def test_v_option(dye_cmdline, capsys):
    exit_code = dye_cmdline("-v")
    assert exit_code == Dye.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "dye" in out


def test_h_and_v_option(dye_cmdline, capsys):
    exit_code = dye_cmdline("-h -v")
    assert exit_code == Dye.EXIT_USAGE
    out, err = capsys.readouterr()
    assert not out
    # this message comes from argparse, we can't modify it
    assert "not allowed with argument" in err


def test_no_command(dye_cmdline, capsys):
    # this should show the usage message
    exit_code = dye_cmdline(None)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_USAGE
    assert not out
    # if you don't give a command, that's a usage error
    # so the usage message goes on standard error
    # check a few things in the usage message
    assert "apply" in err
    assert "preview" in err
    assert "--no-color" in err
    assert "-v" in err


def test_help_command(dye_cmdline, capsys):
    # this should show the usage message
    exit_code = dye_cmdline("help")
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_SUCCESS
    assert not err
    # if you ask for help, help should be on standard output
    assert "apply" in out
    assert "preview" in out
    assert "--no-color" in out
    assert "-v" in out


def test_unknown_command(dye_cmdline, capsys):
    # these errors are all raised and generated by argparse
    exit_code = dye_cmdline("unknowncommand")
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_USAGE
    assert not out
    assert "error" in err
    assert "invalid choice" in err


#
# test Dye.main(), the entry point for the command line script
#
def test_dye_main(mocker):
    # we are just testing main() here, as long as it dispatches, we don't
    # care what the dispatch_list() function returns in this test
    dmock = mocker.patch("dye.Dye.command_agents")
    dmock.return_value = Dye.EXIT_SUCCESS
    assert Dye.main(["agents"]) == Dye.EXIT_SUCCESS


def test_dye_main_unknown_command():
    assert Dye.main(["unknowncommand"]) == Dye.EXIT_USAGE


def test_dispatch_unknown_command(capsys):
    # but by calling dispatch() directly, we can get our own errors
    # first we have to parse valid args
    dye = Dye()
    parser = dye.argparser()
    args = parser.parse_args(["agents"])
    # and then substitute a fake command
    args.command = "fredflintstone"
    exit_code = dye.dispatch("dye", args)
    out, err = capsys.readouterr()
    assert exit_code == Dye.EXIT_USAGE
    assert not out
    assert "unknown command" in err


def test___main__(mocker):
    mocker.patch("dye.Dye.main", return_value=42)
    mocker.patch.object(mainmodule, "__name__", "__main__")
    with pytest.raises(SystemExit) as excinfo:
        mainmodule.doit()
    # unpack the exception to see if got the return value
    assert excinfo.value.code == 42
