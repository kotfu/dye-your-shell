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
"""the 'dye' command line tool for maintaining and switching color schemes"""

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

from .agents import AgentBase
from .exceptions import DyeError
from .theme import Theme
from .utils import AssertBool
from .version import version_string


class Dye(AssertBool):
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
            description="activate a theme",
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
        nocolor_help = "disable color in help output, overrides $DYE_COLORS"
        cgroup.add_argument(
            "--no-color", dest="nocolor", action="store_true", help=nocolor_help
        )
        color_help = "provide a color specification for help output"
        cgroup.add_argument("--color", metavar="<colorspec>", help=color_help)

        forcecolor_help = (
            "force color output even if standard output is not a terminal"
            " (i.e. if it's a file or a pipe to less)"
        )
        parser.add_argument("--force-color", action="store_true", help=forcecolor_help)
        # how to specify a theme
        #        tgroup = parser.add_mutually_exclusive_group()
        #        theme_help = "specify a theme by name from $DYE_DIR/themes"
        #        tgroup.add_argument("-t", "--theme", metavar="<name>", help=theme_help)
        #        file_help = "specify a file containing a theme"
        #        tgroup.add_argument("-f", "--file", metavar="<path>", help=file_help)

        subparsers = parser.add_subparsers(
            dest="command",
            title="arguments",
            metavar="<command>",
            required=False,
            help="command to perform, which must be one of the following:",
        )

        # activate command
        activate_help = "activate a theme"
        activate_parser = subparsers.add_parser(
            "activate",
            help=activate_help,
        )
        scope_help = "only activate the given scope"
        activate_parser.add_argument("-s", "--scope", help=scope_help)
        comment_help = "add comments to the generated shell output"
        activate_parser.add_argument(
            "-c", "--comment", action="store_true", help=comment_help
        )

        # preview command
        preview_help = "show a preview of the styles in a theme"
        preview_parser = subparsers.add_parser(
            "preview",
            description=preview_help,
            formatter_class=RichHelpFormatter,
            help=preview_help,
        )
        theme_group = preview_parser.add_mutually_exclusive_group()
        themefile_help = "specify a file containing a theme"
        theme_group.add_argument(
            "-t", "--themefile", metavar="<path>", help=themefile_help
        )
        themename_help = "specify a theme by name from $DYE_DIR/themes"
        theme_group.add_argument(
            "-n", "--themename", metavar="<name>", help=themename_help
        )

        # agents command
        agents_help = "list all known agents"
        subparsers.add_parser(
            "agents",
            description=agents_help,
            formatter_class=RichHelpFormatter,
            help=agents_help,
        )

        # themes command
        themes_help = "list available themes"
        subparsers.add_parser(
            "themes",
            description=themes_help,
            formatter_class=RichHelpFormatter,
            help=themes_help,
        )

        # help command
        help_help = "display this usage message"
        subparsers.add_parser(
            "help",
            description=help_help,
            formatter_class=RichHelpFormatter,
            help=help_help,
        )

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
        thm = cls(force_color=args.force_color)
        return thm.dispatch(parser.prog, args)

    #
    # initialization and properties
    #
    def __init__(self, force_color=False):
        """Construct a new Themer object

        console
        """

        self.console = rich.console.Console(
            soft_wrap=True,
            markup=False,
            emoji=False,
            highlight=False,
            force_terminal=force_color,
        )
        self.error_console = rich.console.Console(
            stderr=True,
            soft_wrap=True,
            markup=False,
            emoji=False,
            highlight=False,
            force_terminal=force_color,
        )

    @property
    def dye_dir(self):
        """Get the dye configuration directory from the shell environment"""
        try:
            ddir = pathlib.Path(os.environ["DYE_DIR"])
        except KeyError as exc:
            raise DyeError("environment variable DYE_DIR not set") from exc
        if not ddir.is_dir():
            raise DyeError(f"{ddir}: no such directory")
        return ddir

    @property
    def dye_theme_dir(self):
        """Get the dye themes directory"""
        # TODO write unit tests for this
        tdir = self.dye_dir / "themes"
        if not tdir.is_dir():
            raise DyeError(f"{tdir}: no such directory")
        return tdir

    #
    # methods to process command line arguments and dispatch them
    # to the appropriate methods for execution
    #
    def dispatch(self, prog, args):
        """process and execute all the arguments and options"""
        # set the color output options
        self.set_output_colors(args)

        # now go process everything
        try:
            if args.command == "activate":
                exit_code = self.dispatch_activate(args)
            elif args.command == "preview":
                exit_code = self.command_preview(args)
            elif args.command == "agents":
                exit_code = self.command_agents(args)
            elif args.command == "themes":
                exit_code = self.command_themes(args)
            elif args.version:
                print(f"{prog} {version_string()}")
                exit_code = self.EXIT_SUCCESS
            elif args.help or args.command == "help" or not args.command:
                self.argparser().print_help()
                exit_code = self.EXIT_SUCCESS
            else:
                print(f"{prog}: {args.command}: unknown command", file=sys.stderr)
                exit_code = self.EXIT_USAGE
        except DyeError as err:
            self.error_console.print(f"{prog}: {err}")
            exit_code = self.EXIT_ERROR

        return exit_code

    def set_output_colors(self, args):
        """set the colors for help output

        if args has a --colors argument, use that
        if not, use the contents of DYE_COLORS env variable

        DYE_COLORS=args=red bold on black:groups=white on red:

        or --colors='args=red bold on black:groups=white on red'
        """
        colors = {}
        try:
            env_colors = os.environ["DYE_COLORS"]
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
            # overrides DYE_COLORS, making it easy
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
    def load_theme_from_args(self, args):
        """Load a theme from the command line args

        Resolution order:
        1. --themefile, -t from the command line
        2. --themename, -n from the command line
        3. $DYE_THEME_FILE environment variable

        This returns a theme object

        :raises: an exception if we can't find a theme file

        """
        fname = None

        if args.themefile:
            fname = args.themefile
        elif args.themename:
            fname = self.dye_theme_dir / args.themename
            if not fname.is_file():
                fname = self.dye_theme_dir / f"{args.themename}.toml"
                if not fname.is_file():
                    raise DyeError(f"{args.themename}: theme not found")
        else:
            with contextlib.suppress(KeyError):
                fname = pathlib.Path(os.environ["DYE_THEME_FILE"])
        if not fname:
            raise DyeError("no theme specified")

        with open(fname, "rb") as file:
            theme = Theme.load(file, filename=fname)
        return theme

    #
    # functions for the various commands called by dispatch()
    #
    def dispatch_activate(self, args):
        """render the output for given scope(s), or all scopes if none specified

        output is suitable for bash eval $()
        """
        # pylint: disable=too-many-branches
        self.load_theme_from_args(args)

        if args.scope:
            to_activate = args.scope.split(",")
        else:
            to_activate = []
            try:
                for scope in self.theme.definition["scope"]:
                    to_activate.append(scope)
            except KeyError:
                pass

        for scope in to_activate:
            # checking here in case they supplied a scope on the command line that
            # doesn't exist
            if self.theme.has_scope(scope):
                scopedef = self.theme.scopedef_for(scope)
                # find the agent for this scope
                try:
                    agent = scopedef["agent"]
                except KeyError as exc:
                    errmsg = f"{self.prog}: scope '{scope}' does not have an agent."
                    raise DyeError(errmsg) from exc
                # check if the scope is disabled
                if not self.theme.is_enabled(scope):
                    if args.comment:
                        print(f"# [scope.{scope}] skipped because it is not enabled")
                    continue
                # scope is enabled, so print the comment
                if args.comment:
                    print(f"# [scope.{scope}]")

                try:
                    # go get the apropriate class for the agent
                    gcls = AgentBase.classmap[agent]
                    # initialize the class with the scope and scope definition
                    ginst = gcls(
                        scopedef,
                        self.theme.styles,
                        self.theme.variables,
                        prog=self.prog,
                        scope=scope,
                    )
                    # run the agent, printing any shell commands it returns
                    output = ginst.run()
                    if output:
                        print(output)
                except KeyError as exc:
                    raise DyeError(f"{self.prog}: {agent}: unknown agent") from exc
            else:
                raise DyeError(f"{self.prog}: {scope}: no such scope")
        return self.EXIT_SUCCESS

    def command_preview(self, args):
        """Display a preview of the styles in a theme"""
        theme = self.load_theme_from_args(args)

        outer_table = rich.table.Table(
            box=None, expand=True, show_header=False, padding=0
        )

        # output some basic information about the theme
        summary_table = rich.table.Table(
            box=None, expand=False, show_header=False, padding=(0, 0, 0, 1)
        )
        summary_table.add_row("Theme file:", str(theme.filename))
        try:
            description = theme.definition["description"]
        except KeyError:
            description = ""
        summary_table.add_row("Description:", description)
        try:
            version = theme.definition["type"]
        except KeyError:
            version = ""
        summary_table.add_row("Type:", version)
        try:
            version = theme.definition["version"]
        except KeyError:
            version = ""
        summary_table.add_row("Version:", version)
        outer_table.add_row(summary_table)
        outer_table.add_row("")

        # show all the colors in the palette
        palette_table = rich.table.Table(box=None, expand=False, padding=(0, 0, 0, 1))
        palette_table.add_column("[palette]")
        for color in theme.palette:
            value = theme.definition["palette"][color]
            col1 = rich.text.Text.assemble(("██", value), f" {color}")
            col2 = rich.text.Text(f' = "{value}"')
            palette_table.add_row(col1, col2)
        outer_table.add_row(palette_table)
        outer_table.add_row("")
        outer_table.add_row("")

        # show all the elements of the style
        elements_table = rich.table.Table(box=None, expand=False, padding=(0, 0, 0, 1))
        elements_table.add_column("[elements]")
        for element, style in theme.elements.items():
            value = theme.definition["elements"][element]
            col1 = rich.text.Text(element, style)
            col2 = rich.text.Text(f' = "{value}"')
            elements_table.add_row(col1, col2)
        outer_table.add_row(elements_table)

        # lower_table = rich.table.Table(
        #     box=None,
        #     expand=True,
        #     show_header=False,
        #     padding=(0, 4, 0, 0),
        #     pad_edge=False,
        # )
        # lower_table.add_column(ratio=0.67)
        # lower_table.add_column(ratio=0.33)
        # lower_table.add_row(palette_table, elements_table)

        # outer_table.add_row(lower_table)

        # the text style here makes the whole panel print with the foreground
        # and background colors from the style
        self.console.print(rich.panel.Panel(outer_table, style=theme.elements["text"]))
        return self.EXIT_SUCCESS

    def command_agents(self, _):
        """list all available agents and a short description of each"""
        # ignore all other args
        agents = {}
        for name, clss in AgentBase.classmap.items():
            desc = inspect.getdoc(clss)
            if desc:
                desc = desc.split("\n", maxsplit=1)[0]
            agents[name] = desc

        table = rich.table.Table(
            box=rich.box.SIMPLE_HEAD, show_edge=False, pad_edge=False
        )
        table.add_column("Agent")
        table.add_column("Description")

        for agent in sorted(agents):
            table.add_row(agent, agents[agent])
        self.console.print(table)

        return self.EXIT_SUCCESS

    def command_themes(self, _):
        """Print a list of all themes"""
        # ignore all other args
        themeglob = self.dye_theme_dir.glob("*.toml")
        themes = []
        for theme in themeglob:
            themes.append(theme.stem)
        themes.sort()
        for theme in themes:
            print(theme)
        return self.EXIT_SUCCESS
