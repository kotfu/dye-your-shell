#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Jared Crapo
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
Entry point for 'shell-themekit' command line program.
"""
import argparse
import pathlib
import os
import sys
import textwrap
import tomllib

from shell_themekit import Theme

import rich.color
import rich.console

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def _build_parser():
    """Build the argument parser"""
    parser = argparse.ArgumentParser(
        description="Generate shell code to activate a theme"
    )
    theme_help = "specify a theme directory"
    parser.add_argument("-t", "--theme", help=theme_help)

    domain_help = "domain to generate output for"
    parser.add_argument("domain", nargs='*', help=domain_help)

    return parser


def main(argv=None):
    """Entry point for 'shell-themekit' command line program.

    :param argv:    pass a list of arguments to be processed. If None, sys.argv[1:]
                    will be used. To process with no arguments, pass an empty list.
    """

    parser = _build_parser()
    args = parser.parse_args(argv)

    thm = Theme(parser.prog)
    thm.load(args.theme)
    return thm.render(args.domain)


if __name__ == "__main__":  # pragma: nocover
    sys.exit(main())
