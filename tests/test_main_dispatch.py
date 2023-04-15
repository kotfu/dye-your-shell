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

import os

import pytest
from rich_argparse import RichHelpFormatter

from shell_themer import Themer


#
# test output color logic
#
def test_output_color_cmdline(thm_cmdline, mocker):
    # command line color arguments should override
    # all environment variables
    RichHelpFormatter.styles["argparse.text"] == "#000000"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"SHELL_THEMER_COLORS": "text=#f0f0f0"})
    mocker.patch.dict(os.environ, {"NO_COLOR": "doesn't matter"})
    argv = [
        "--help",
        "--color=text=#ffff00:args=#bd93f9:metavar=#f8f8f2 on #44475a bold",
    ]
    thm_cmdline(argv)
    assert RichHelpFormatter.styles["argparse.text"] == "#ffff00"
    assert RichHelpFormatter.styles["argparse.args"] == "#bd93f9"
    assert RichHelpFormatter.styles["argparse.metavar"] == "#f8f8f2 on #44475a bold"


def test_output_color_no_color(thm_cmdline, mocker):
    mocker.patch.dict(os.environ, {}, clear=True)
    RichHelpFormatter.styles["argparse.text"] == "#ff00ff"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"NO_COLOR": "doesn't matter"})
    thm_cmdline("--help")
    for element in Themer.HELP_ELEMENTS:
        assert RichHelpFormatter.styles[f"argparse.{element}"] == "default"


def test_output_color_envs_only(thm_cmdline, mocker):
    # NO_COLOR should override SHELL_THEMER_COLORS
    RichHelpFormatter.styles["argparse.text"] == "#ff00ff"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"SHELL_THEMER_COLORS": "text=#f0f0f0"})
    mocker.patch.dict(os.environ, {"NO_COLOR": "doesn't matter"})
    thm_cmdline("--help")
    for element in Themer.HELP_ELEMENTS:
        assert RichHelpFormatter.styles[f"argparse.{element}"] == "default"


def test_output_color_env_color(thm_cmdline, mocker):
    # SHELL_THEMER_COLORS should override default colors
    RichHelpFormatter.styles["argparse.text"] == "#ff00ff"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"SHELL_THEMER_COLORS": "text=#f0f0f0"})
    thm_cmdline("--help")
    assert RichHelpFormatter.styles["argparse.text"] == "#f0f0f0"


def test_output_color_env_empty(thm_cmdline, mocker):
    # SHELL_THEMER_COLORS should override default colors
    RichHelpFormatter.styles["argparse.text"] == "#ff00ff"
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"SHELL_THEMER_COLORS": ""})
    thm_cmdline("--help")
    assert RichHelpFormatter.styles["argparse.text"] == "default"


#
# test unknown commands, no commands, help, and version
#
def test_help_option(thm_cmdline, capsys):
    exit_code = thm_cmdline("--help")
    assert exit_code == Themer.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "preview" in out
    assert "--no-color" in out


def test_h_option(thm_cmdline, capsys):
    exit_code = thm_cmdline("-h")
    assert exit_code == Themer.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "preview" in out
    assert "--no-color" in out


def test_version_option(thm_cmdline, capsys):
    exit_code = thm_cmdline("--version")
    assert exit_code == Themer.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "shell-themer" in out


def test_v_option(thm_cmdline, capsys):
    exit_code = thm_cmdline("-v")
    assert exit_code == Themer.EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert not err
    assert "shell-themer" in out


def test_no_command(thm_cmdline, capsys):
    # this should show the usage message
    exit_code = thm_cmdline(None)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_USAGE
    assert not out
    # check a few things in the usage message
    assert "generate" in err
    assert "--theme" in err


def test_help_command(thm_cmdline, capsys):
    # this should show the usage message
    exit_code = thm_cmdline("help")
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    # check a few things in the usage message
    assert "generate" in out
    assert "--theme" in out


def test_unknown_command(thm_cmdline, capsys):
    # these errors are all raised and generated by argparse
    exit_code = thm_cmdline("unknowncommand")
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_USAGE
    assert not out
    assert "error" in err
    assert "invalid choice" in err


def test_dispatch_unknown_command(thm, capsys):
    # but by calling dispatch() directly, we can get our own errors
    # first we have to parse valid args
    parser = thm.argparser()
    args = parser.parse_args(["list"])
    # and then substitute a fake command
    args.command = "fredflintstone"
    exit_code = thm.dispatch(args)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_USAGE
    assert not out
    assert "unknown command" in err


#
# test Themer.main(), the entry point for the command line script
#
def test_themer_main(mocker):
    # we are just testing main() here, as long as it dispatches, we don't
    # care what the dispatch_list() function returns in this test
    dmock = mocker.patch("shell_themer.Themer.dispatch_list")
    dmock.return_value = Themer.EXIT_SUCCESS
    assert Themer.main(["list"]) == Themer.EXIT_SUCCESS


def test_themer_main_unknown_command():
    assert Themer.main(["unknowncommand"]) == Themer.EXIT_USAGE


def test___main__(mocker):
    from shell_themer import __main__ as mainmodule

    mocker.patch("shell_themer.Themer.main", return_value=42)
    mocker.patch.object(mainmodule, "__name__", "__main__")
    with pytest.raises(SystemExit) as excinfo:
        mainmodule.doit()
    # unpack the exception to see if got the return value
    assert excinfo.value.code == 42
