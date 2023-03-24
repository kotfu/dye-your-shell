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

import shell_themekit

import rich.color
import rich.console

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def _build_parser():
    """Build the argument parser"""
    parser = argparse.ArgumentParser(
        description="Retrieve the color of a given theme scope"
    )
    theme_help = "specify a theme directory"
    parser.add_argument("-t", "--theme", help=theme_help)

    format_help = "format for the output"
    parser.add_argument("-f", "--format", default="keyvalue", choices=["keyvalue"] ,help=theme_help)

    scope_help = "scope to generate color schemes for"
    parser.add_argument("scope", help=scope_help)

    return parser




def _get_color(theme, domain, element):
    """get a color from the theme"""
    color = theme["scopes"][domain][element]

    try:
        color = theme["styles"][color]
    except KeyError:
        pass
    clr = rich.color.Color.parse(color)
    return clr



def main(argv=None):

    console = rich.console.Console()

    parser = _build_parser()
    args = parser.parse_args(argv)

    # get the theme
    theme_file = args.theme
    if not theme_file:
        try:
            theme_file = pathlib.Path(os.environ["THEME_DIR"]) / "theme.toml"
        except KeyError:
            console.print(f"{parser.prog}: no theme found")
            sys.exit(1)

    with open(theme_file, 'rb') as file:
        theme = tomllib.load(file)

    if '.' in args.scope:
        (domain, element) = args.scope.split('.')
    else:
        domain = args.scope
        element = None


    # get the list of matching scopes
    scopes=[]
    try:
        if element:
            # just get one element
            scopes.append((f"{domain}.{element}", _get_color(theme, domain, element)))
        else:
            # get all the elements in the domain
            for element in theme["scopes"][domain]:
                scopes.append((f"{domain}.{element}", _get_color(theme, domain, element)))
    except KeyError:
        console.print(f"{parser.prog}: '{args.scope}' not found")
        return 1


    # render the output
    if args.format == "keyvalue":
        for (scope, clr) in scopes:
            console.print(f"{scope}:{clr.name}")
            

if __name__ == "__main__":  # pragma: nocover
    sys.exit(main())
