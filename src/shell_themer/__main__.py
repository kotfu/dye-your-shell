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
"""
Entry point for 'shell-themer' command line program.
"""
import argparse
import pathlib
import os
import sys
import textwrap
import tomllib

from shell_themer import Themer, VERSION_STRING

import rich.color
import rich.console

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def build_parser():
    """Build the argument parser"""
    parser = argparse.ArgumentParser(
        description="Generate shell code to activate a theme"
    )

    version_help = "show the program version and exit"
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION_STRING,
        help=version_help,
    )
    tgroup = parser.add_mutually_exclusive_group()
    theme_help = "specify a theme by name from $THEME_DIR"
    tgroup.add_argument("-t", "--theme", help=theme_help)
    file_help = "specify a file containing a theme"
    tgroup.add_argument("-f", "--file", help=file_help)
    subparsers = parser.add_subparsers(
        dest="command", help="sub-command help and stuff", required=True
    )

    themes_parser = subparsers.add_parser("themes", help="list all themes")

    preview_parser = subparsers.add_parser("preview", help="preview styles in a theme")

    generate_parser = subparsers.add_parser(
        "generate",
        help="generate shell code to make the theme effective in your environment",
    )
    scope_help = "only generate the given scope"
    generate_parser.add_argument("-s", "--scope", help=scope_help)
    comment_help = "add comments to the generated output"
    generate_parser.add_argument(
        "-c", "--comment", action="store_true", help=comment_help
    )

    return parser


def main(argv=None):
    """Entry point for 'shell-themer' command line program.

    :param argv:    pass a list of arguments to be processed. If None, sys.argv[1:]
                    will be used. To process with no arguments, pass an empty list.
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    thm = Themer(parser.prog)
    return thm.dispatch(args)


if __name__ == "__main__":  # pragma: nocover
    sys.exit(main())
