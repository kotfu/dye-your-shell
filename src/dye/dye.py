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

import rich.box
import rich.color
import rich.console
import rich.errors
import rich.layout
import rich.style
from rich_argparse import RichHelpFormatter

from .agents import AgentBase
from .exceptions import DyeError, DyeSyntaxError
from .pattern import Pattern
from .theme import Theme
from .version import version_string


class Dye:
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
            description=(
                "activate color output in shell commands using themes and patterns"
            ),
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

        # set up for the sub commands
        subparsers = parser.add_subparsers(
            dest="command",
            title="arguments",
            metavar="<command>",
            required=False,
            help="command to perform, which must be one of the following:",
        )

        # apply command
        apply_help = "apply a theme"
        apply_parser = subparsers.add_parser(
            "apply",
            description=apply_help,
            formatter_class=RichHelpFormatter,
            help=apply_help,
        )
        pattern_group = apply_parser.add_mutually_exclusive_group()
        pattern_file_help = "specify a file containing a pattern"
        pattern_group.add_argument(
            "-f", "--patternfile", metavar="<path>", help=pattern_file_help
        )
        pattern_name_help = "specify a pattern by name from $DYE_DIR"
        pattern_group.add_argument(
            "-p", "--patternname", metavar="<name>", help=pattern_name_help
        )
        theme_group = apply_parser.add_mutually_exclusive_group()
        theme_file_help = "specify a file containing a theme"
        theme_group.add_argument(
            "-t", "--themefile", metavar="<path>", help=theme_file_help
        )
        theme_name_help = "specify a theme by name from $DYE_DIR/themes"
        theme_group.add_argument(
            "-n", "--themename", metavar="<name>", help=theme_name_help
        )

        scope_help = "only apply the given scope"
        apply_parser.add_argument("-s", "--scope", help=scope_help)
        comment_help = "add comments to the generated shell output"
        apply_parser.add_argument(
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
        theme_file_help = "specify a file containing a theme"
        theme_group.add_argument(
            "-t", "--themefile", metavar="<path>", help=theme_file_help
        )
        theme_name_help = "specify a theme by name from $DYE_DIR/themes"
        theme_group.add_argument(
            "-n", "--themename", metavar="<name>", help=theme_name_help
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
        """Construct a new Dye object"""

        self.console = self._create_console(force_color)
        self.error_console = self._create_error_console(force_color)

    def _create_console(self, force_color):
        """create a rich console object to be used for output

        we have this as a separate method so that it can be patched
        in our test suite
        """
        # force_terminal can be True, False, or None
        # argparse will always set it to be True or False
        # we need it to be True or None
        if not force_color:
            force_color = None
        return rich.console.Console(
            soft_wrap=True,
            markup=False,
            emoji=False,
            highlight=False,
            force_terminal=force_color,
        )

    def _create_error_console(self, force_color):
        """create a rich console object to be used for std err

        we have this as a separate method so that it can be patched
        in our test suite
        """
        # force_terminal can be True, False, or None
        # argparse will always set it to be True or False
        # we need it to be True or None
        if not force_color:
            force_color = None
        return rich.console.Console(
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
        # TODO write unit tests for this
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
        self.set_help_colors(args)

        # now go process everything (order matters)
        try:
            if args.help or args.command == "help":
                self.console.print(self.argparser().format_help())
                exit_code = self.EXIT_SUCCESS
            elif args.version:
                print(f"{prog} {version_string()}")
                exit_code = self.EXIT_SUCCESS
            elif not args.command:
                # this is a usage error, so it goes to stderr
                self.error_console.print(self.argparser().format_help())
                exit_code = self.EXIT_USAGE
            elif args.command == "apply":
                exit_code = self.command_apply(args)
            elif args.command == "preview":
                exit_code = self.command_preview(args)
            elif args.command == "agents":
                exit_code = self.command_agents(args)
            elif args.command == "themes":
                exit_code = self.command_themes(args)
            else:
                self.error_console.print(f"{prog}: {args.command}: unknown command")
                exit_code = self.EXIT_USAGE
        except (DyeError, DyeSyntaxError) as err:
            self.error_console.print(f"{prog}: {err}")
            exit_code = self.EXIT_ERROR

        return exit_code

    def set_help_colors(self, args):
        """set the colors for help output

        if args has a --colors argument, use that
        if not, use the contents of DYE_COLORS env variable

        DYE_COLORS=args=red bold on black:groups=white on red:

        or --colors='args=red bold on black:groups=white on red'
        """
        help_styles = {}
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
            help_styles = self._parse_colorspec(args.color)
        elif args.nocolor:
            # disable the default color output
            help_styles = self._parse_colorspec("")
        elif env_colors:
            # was set, and was set to a non-empty string
            help_styles = self._parse_colorspec(env_colors)

        # now map this all into rich.styles
        for key, value in help_styles.items():
            RichHelpFormatter.styles[f"argparse.{key}"] = value

    def _parse_colorspec(self, colorspec):
        "parse colorspec into a dictionary of styles"
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
    # functions for the various commands called by dispatch()
    #
    def command_apply(self, args):
        """apply a pattern

        many agents just output to standard output, which we rely on a shell
        wrapper to execute for us. agents can also write/move files,
        replace files or whatever else they are gonna do

        output is suitable for `source < $(dye apply)`
        """
        # pylint: disable=too-many-branches
        theme = self.load_theme_from_args(args, required=False)
        pattern = self.load_pattern_from_args(args)
        pattern.process(theme)
        # pattern now has everything in it we need

        if args.scope:
            to_activate = args.scope.split(",")
        else:
            to_activate = []
            try:
                for scope in pattern.definition["scopes"]:
                    to_activate.append(scope)
            except KeyError:
                pass

        for scope in to_activate:
            # checking here in case they supplied a scope on the command line that
            # doesn't exist
            if pattern.has_scope(scope):
                scopedef = pattern.scopes[scope]
                # find the agent for this scope
                try:
                    agent_name = scopedef["agent"]
                except KeyError as exc:
                    errmsg = f"scope '{scope}' does not have an agent."
                    raise DyeError(errmsg) from exc
                # check if the scope is disabled
                if not pattern.is_scope_enabled(scope):
                    if args.comment:
                        print(f"# scope '{scope}' skipped because it is not enabled")
                    continue
                # scope is enabled, so print the comment
                if args.comment:
                    print(f"# scope '{scope}'")

                try:
                    # go get the apropriate class for the agent
                    agent_cls = AgentBase.classmap[agent_name]
                    # initialize the class with the scope and scope definition
                    agent = agent_cls(scope, pattern)
                    # run the agent, printing any shell commands it returns
                    output = agent.run()
                    if output:
                        print(output)
                except KeyError as exc:
                    raise DyeError(f"{agent_name}: unknown agent") from exc
            else:
                raise DyeError(f"{scope}: no such scope")
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

        # show all the colors
        colors_table = rich.table.Table(box=None, expand=False, padding=(0, 0, 0, 1))
        colors_table.add_column("[colors]")
        for color in theme.colors:
            value = theme.definition["colors"][color]
            col1 = rich.text.Text.assemble(("██", value), f" {color}")
            col2 = rich.text.Text(f' = "{value}"')
            colors_table.add_row(col1, col2)
        outer_table.add_row(colors_table)
        outer_table.add_row("")
        outer_table.add_row("")

        # show all the styles
        styles_table = rich.table.Table(box=None, expand=False, padding=(0, 0, 0, 1))
        styles_table.add_column("[styles]")
        for name, style in theme.styles.items():
            value = theme.definition["styles"][name]
            col1 = rich.text.Text(name, style)
            col2 = rich.text.Text(f' = "{value}"')
            styles_table.add_row(col1, col2)
        outer_table.add_row(styles_table)

        # the text style here makes the whole panel print with the foreground
        # and background colors from the style
        try:
            text_style = theme.styles["text"]
        except KeyError as exc:
            raise DyeSyntaxError("theme must define a 'text' style") from exc
        self.console.print(rich.panel.Panel(outer_table, style=text_style))
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

    #
    # supporting methods
    #
    def load_theme_from_args(self, args, required=True):
        """Load a theme from the command line args

        required - whether we have to have a theme file or not
                if required=False an empty theme can be returned

        Will raise an exception if args specify a file and it
        doesn't exist or can't be opened

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

        if fname:
            with open(fname, "rb") as file:
                theme = Theme.load(file, filename=fname)
            return theme

        if required:
            raise DyeError("no theme specified")

        return Theme()

    def load_pattern_from_args(self, args):
        """load, but don't process/execute the pattern

        Resolution order:
        1. --patternfile -f from the command line
        2. --patternname, -p from the command line
        3. $DYE_PATTERN_FILE environment variable

        This returns a pattern object

        :raises: an exception if we can't find a pattern file

        """
        fname = None

        if args.patternfile:
            fname = args.patternfile
        elif args.patternname:
            fname = self.dye_theme_dir / args.patternname
            if not fname.is_file():
                fname = self.dye_theme_dir / f"{args.patternname}.toml"
                if not fname.is_file():
                    raise DyeError(f"{args.patternname}: pattern not found")
        else:
            with contextlib.suppress(KeyError):
                fname = pathlib.Path(os.environ["DYE_PATTERN_FILE"])
        if not fname:
            raise DyeError("no pattern specified")

        with open(fname, "rb") as fobj:
            pattern = Pattern.load(fobj)
        return pattern
