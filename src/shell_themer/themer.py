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
"""command line tool for maintaining and switching color schemes"""

import argparse
import contextlib
import inspect
import os
import pathlib
import sys

import rich.box
import rich.color
import rich.console
import rich.errors
import rich.layout
import rich.style
from rich_argparse import RichHelpFormatter

from .exceptions import ThemeError
from .generators import GeneratorBase
from .theme import Theme
from .utils import AssertBool
from .version import version_string


class Themer(AssertBool):
    """parse and translate a theme file for various command line programs"""

    EXIT_SUCCESS = 0
    EXIT_ERROR = 1
    EXIT_USAGE = 2

    HELP_ELEMENTS = ["args", "groups", "help", "metavar", "prog", "syntax", "text"]

    #
    # methods for running from the command line
    #
    @classmethod
    def argparser(cls):
        """Build the argument parser"""

        RichHelpFormatter.usage_markup = True
        RichHelpFormatter.group_name_formatter = str.lower

        parser = argparse.ArgumentParser(
            description="generate shell code to activate a theme",
            formatter_class=RichHelpFormatter,
            add_help=False,
            epilog=(
                "type  '[argparse.prog]%(prog)s[/argparse.prog]"
                " [argparse.args]<command>[/argparse.args] -h' for command"
                " specific help"
            ),
        )

        hgroup = parser.add_mutually_exclusive_group()
        help_help = "show this help message and exit"
        hgroup.add_argument(
            "-h",
            "--help",
            action="store_true",
            help=help_help,
        )
        version_help = "show the program version and exit"
        hgroup.add_argument(
            "-v",
            "--version",
            action="store_true",
            help=version_help,
        )

        # colors
        cgroup = parser.add_mutually_exclusive_group()
        nocolor_help = "disable color in help output"
        cgroup.add_argument(
            "--no-color", dest="nocolor", action="store_true", help=nocolor_help
        )
        color_help = "provide a color specification"
        cgroup.add_argument("--color", metavar="<colorspec>", help=color_help)

        # how to specify a theme
        tgroup = parser.add_mutually_exclusive_group()
        theme_help = "specify a theme by name from $THEME_DIR"
        tgroup.add_argument("-t", "--theme", metavar="<name>", help=theme_help)
        file_help = "specify a file containing a theme"
        tgroup.add_argument("-f", "--file", metavar="<path>", help=file_help)

        # the commands
        subparsers = parser.add_subparsers(
            dest="command",
            title="arguments",
            metavar="<command>",
            required=False,
            help="action to perform, which must be one of the following:",
        )

        generate_help = (
            "generate shell code to make the theme effective in your environment"
        )
        generate_parser = subparsers.add_parser(
            "generate",
            help=generate_help,
        )
        scope_help = "only generate the given scope"
        generate_parser.add_argument("-s", "--scope", help=scope_help)
        comment_help = "add comments to the generated output"
        generate_parser.add_argument(
            "-c", "--comment", action="store_true", help=comment_help
        )

        generators_help = "list all known generators"
        subparsers.add_parser("generators", help=generators_help)

        list_help = "list all themes in $THEMES_DIR"
        subparsers.add_parser("list", help=list_help)

        preview_help = "show a preview of the styles in a theme"
        subparsers.add_parser("preview", help=preview_help)

        help_help = "display this usage message"
        subparsers.add_parser("help", help=help_help)

        return parser

    @classmethod
    def main(cls, argv=None):
        """Entry point from the command line

        parse arguments and call dispatch() for processing
        """

        parser = cls.argparser()
        try:
            args = parser.parse_args(argv)
        except SystemExit as exc:
            return exc.code

        # create an instance of ourselves
        thm = cls(parser.prog)
        return thm.dispatch(args)

    #
    # initialization and properties
    #
    def __init__(self, prog):
        """Construct a new Themer object

        console
        """

        self.prog = prog
        self.console = rich.console.Console(
            soft_wrap=True,
            markup=False,
            emoji=False,
            highlight=False,
        )
        self.error_console = rich.console.Console(
            stderr=True,
            soft_wrap=True,
            markup=False,
            emoji=False,
            highlight=False,
        )

        self.theme = Theme(self.prog)

    @property
    def theme_dir(self):
        """Get the theme directory from the shell environment"""
        try:
            tdir = pathlib.Path(os.environ["THEME_DIR"])
        except KeyError as exc:
            raise ThemeError(f"{self.prog}: $THEME_DIR not set") from exc
        if not tdir.is_dir():
            raise ThemeError(f"{self.prog}: {tdir}: no such directory")
        return tdir

    #
    # methods to process command line arguments and dispatch them
    # to the appropriate methods for execution
    #
    def dispatch(self, args):
        """process and execute all the arguments and options"""
        # set the color output options
        self.set_output_colors(args)

        # now go process everything
        try:
            if args.help or args.command == "help":
                self.argparser().print_help()
                exit_code = self.EXIT_SUCCESS
            elif args.version:
                print(f"{self.prog} {version_string()}")
                exit_code = self.EXIT_SUCCESS
            elif not args.command:
                self.argparser().print_help(sys.stderr)
                exit_code = self.EXIT_USAGE
            elif args.command == "list":
                exit_code = self.dispatch_list(args)
            elif args.command == "preview":
                exit_code = self.dispatch_preview(args)
            elif args.command == "generate":
                exit_code = self.dispatch_generate(args)
            elif args.command == "generators":
                exit_code = self.dispatch_generators(args)
            else:
                print(f"{self.prog}: {args.command}: unknown command", file=sys.stderr)
                exit_code = self.EXIT_USAGE
        except ThemeError as err:
            self.error_console.print(err)
            exit_code = self.EXIT_ERROR

        return exit_code

    def set_output_colors(self, args):
        """set the colors for generated output

        if args has a --colors argument, use that
        if not, use the contents of SHELL_THEMER_COLORS env variable

        SHELL_THEMER_COLORS=args=red bold on black:groups=white on red:

        or --colors='args=red bold on black:groups=white on red'
        """
        colors = {}
        try:
            env_colors = os.environ["SHELL_THEMER_COLORS"]
            if not env_colors:
                # if it's set to an empty string that means we shouldn't
                # show any colors
                args.nocolor = True
        except KeyError:
            # wasn't set
            env_colors = None

        # https://no-color.org/
        try:
            _ = os.environ["NO_COLOR"]
            # overrides SHELL_THEMER_COLORS, making it easy
            # to turn off colors for a bunch of tools
            args.nocolor = True
        except KeyError:
            # don't do anything
            pass

        if args.color:
            # overrides environment variables
            colors = self._parse_colorspec(args.color)
        elif args.nocolor:
            # disable the default color output
            colors = self._parse_colorspec("")
        elif env_colors:
            # was set, and was set to a non-empty string
            colors = self._parse_colorspec(env_colors)

        # now map this all into rich.styles
        for key, value in colors.items():
            RichHelpFormatter.styles[f"argparse.{key}"] = value

    def _parse_colorspec(self, colorspec):
        "parse colorspec into a dictionary"
        colors = {}
        # set everything to default, ie smash all the default colors
        for element in self.HELP_ELEMENTS:
            colors[element] = "default"

        clauses = colorspec.split(":")
        for clause in clauses:
            parts = clause.split("=", 1)
            if len(parts) == 2:
                element = parts[0]
                styledef = parts[1]
                if element in self.HELP_ELEMENTS:
                    colors[element] = styledef
            else:
                # invalid syntax, too many equals signs
                # ignore this clause
                pass
        return colors

    #
    # loading a theme
    #
    def load_from_args(self, args):
        """Load a theme from the command line args

        Resolution order:
        1. --file from the command line
        2. --theme from the command line
        3. $THEME_FILE environment variable

        This either loads the theme or raises an exception.
        It doesn't return anything

        :raises: an exception if we can't find a theme file

        """
        fname = None
        if args.file:
            fname = args.file
        elif args.theme:
            fname = self.theme_dir / args.theme
            if not fname.is_file():
                fname = self.theme_dir / f"{args.theme}.toml"
                if not fname.is_file():
                    raise ThemeError(f"{self.prog}: {args.theme}: theme not found")
        else:
            with contextlib.suppress(KeyError):
                fname = pathlib.Path(os.environ["THEME_FILE"])
        if not fname:
            raise ThemeError(f"{self.prog}: no theme or theme file specified")

        self.theme = Theme(prog=self.prog)
        with open(fname, "rb") as file:
            self.theme.load(file)
            self.theme.theme_file = fname

    #
    # dispatchers
    #
    def dispatch_list(self, _):
        """Print a list of all themes"""
        # ignore all other args
        themeglob = self.theme_dir.glob("*.toml")
        themes = []
        for theme in themeglob:
            themes.append(theme.stem)
        themes.sort()
        for theme in themes:
            print(theme)
        return self.EXIT_SUCCESS

    def dispatch_preview(self, args):
        """Display a preview of the styles in a theme"""
        self.load_from_args(args)

        mystyles = self.theme.styles.copy()
        try:
            text_style = mystyles["text"]
        except KeyError:
            # if they didn't specify a text style, tell Rich to just use
            # whatever the default is for the terminal
            text_style = "default"
        with contextlib.suppress(KeyError):
            del mystyles["background"]

        outer_table = rich.table.Table(
            box=rich.box.SIMPLE_HEAD, expand=True, show_header=False
        )

        summary_table = rich.table.Table(box=None, expand=True, show_header=False)
        summary_table.add_row("Theme file:", str(self.theme.theme_file))
        try:
            name = self.theme.definition["name"]
        except KeyError:
            name = ""
        summary_table.add_row("Name:", name)
        try:
            version = self.theme.definition["version"]
        except KeyError:
            version = ""
        summary_table.add_row("Version:", version)
        outer_table.add_row(summary_table)
        outer_table.add_row(" ")

        styles_table = rich.table.Table(
            box=rich.box.SIMPLE_HEAD, expand=True, show_edge=False, pad_edge=False
        )
        styles_table.add_column("Styles")
        for name, style in mystyles.items():
            styles_table.add_row(name, style=style)

        scopes_table = rich.table.Table(
            box=rich.box.SIMPLE_HEAD, show_edge=False, pad_edge=False
        )
        scopes_table.add_column("Scope", ratio=0.4)
        scopes_table.add_column("Generator", ratio=0.6)
        try:
            for name, scopedef in self.theme.definition["scope"].items():
                try:
                    generator = scopedef["generator"]
                except KeyError:
                    generator = ""
                scopes_table.add_row(name, generator)
        except KeyError:  # pragma: nocover
            # no scopes defined in the theme
            pass

        lower_table = rich.table.Table(box=None, expand=True, show_header=False)
        lower_table.add_column(ratio=0.45)
        lower_table.add_column(ratio=0.1)
        lower_table.add_column(ratio=0.45)
        lower_table.add_row(styles_table, None, scopes_table)

        outer_table.add_row(lower_table)

        # the text style here makes the whole panel print with the foreground
        # and background colors from the style
        self.console.print(rich.panel.Panel(outer_table, style=text_style))
        return self.EXIT_SUCCESS

    def dispatch_generate(self, args):
        """render the output for given scope(s), or all scopes if none specified

        output is suitable for bash eval $()
        """
        # pylint: disable=too-many-branches
        self.load_from_args(args)

        if args.scope:
            to_generate = args.scope.split(",")
        else:
            to_generate = []
            try:
                for scope in self.theme.definition["scope"]:
                    to_generate.append(scope)
            except KeyError:
                pass

        for scope in to_generate:
            # checking here in case they supplied a scope on the command line that
            # doesn't exist
            if self.theme.has_scope(scope):
                scopedef = self.theme.scopedef_for(scope)
                # find the generator for this scope
                try:
                    generator = scopedef["generator"]
                except KeyError as exc:
                    errmsg = f"{self.prog}: scope '{scope}' does not have a generator."
                    raise ThemeError(errmsg) from exc
                # check if the scope is disabled
                if not self.theme.is_enabled(scope):
                    if args.comment:
                        print(f"# [scope.{scope}] skipped because it is not enabled")
                    continue
                # scope is enabled, so print the comment
                if args.comment:
                    print(f"# [scope.{scope}]")

                try:
                    # go get the apropriate class for the generator
                    gcls = GeneratorBase.classmap[generator]
                    # initialize the class with the scope and scope definition
                    ginst = gcls(
                        scopedef,
                        self.theme.styles,
                        self.theme.variables,
                        prog=self.prog,
                        scope=scope,
                    )
                    # generate and print the output
                    output = ginst.generate()
                    if output:
                        print(output)
                except KeyError as exc:
                    raise ThemeError(
                        f"{self.prog}: {generator}: unknown generator"
                    ) from exc
            else:
                raise ThemeError(f"{self.prog}: {scope}: no such scope")
        return self.EXIT_SUCCESS

    def dispatch_generators(self, _):
        """list all available generators and a short description of each"""
        # ignore all other args
        generators = {}
        for name, clss in GeneratorBase.classmap.items():
            desc = inspect.getdoc(clss)
            if desc:
                desc = desc.split("\n")[0]
            generators[name] = desc

        table = rich.table.Table(
            box=rich.box.SIMPLE_HEAD, show_edge=False, pad_edge=False
        )
        table.add_column("Generator")
        table.add_column("Description")

        for generator in sorted(generators):
            table.add_row(generator, generators[generator])
        self.console.print(table)

        return self.EXIT_SUCCESS
