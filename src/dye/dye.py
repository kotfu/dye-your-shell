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
import rich.rule
import rich.style
from rich_argparse import RichHelpFormatter

from .agents import AgentBase
from .exceptions import DyeError, DyeSyntaxError
from .pattern import Pattern
from .theme import Theme
from .utils import version_string


class Dye:
    """parse and translate a theme file for various command line programs"""

    EXIT_SUCCESS = 0
    EXIT_ERROR = 1
    EXIT_USAGE = 2

    HELP_ELEMENTS = ["args", "groups", "help", "metavar", "prog", "syntax", "text"]

    #
    # initialization and properties
    #
    def __init__(self, force_color=False):
        """Construct a new Dye object"""

        self.debug = False

        self.console = self._create_console(force_color)
        self.error_console = self._create_error_console(force_color)
        self.print_console = self._create_print_console(force_color)

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

    def _create_print_console(self, force_color):
        """create a rich console object to be used for output for the
        print command, which enables console markup

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
            markup=True,
            emoji=False,
            highlight=False,
            force_terminal=force_color,
        )

    @property
    def dye_dir(self):
        """Get the dye configuration directory from the shell environment

        returns a pathlib.Path if $DYE_DIR is set, else None
        """
        try:
            return pathlib.Path(os.environ["DYE_DIR"])
        except KeyError:
            return None

    @property
    def dye_theme_dir(self):
        """Get the dye themes directory

        returns a pathlib.Path if $DYE_DIR is set, else None
        """
        if self.dye_dir:
            return self.dye_dir / "themes"

        return None

    #
    # methods to process command line arguments and dispatch them
    # to the appropriate methods for execution
    #
    def dispatch(self, prog, args):
        """process and execute all the arguments and options"""

        self.debug = args.debug
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
            elif args.command == "print":
                exit_code = self.command_print(args)
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
        except KeyError:
            env_colors = None

        # https://no-color.org/
        try:
            env_no_color = os.environ["NO_COLOR"]
        except KeyError:
            env_no_color = None

        if args.color:
            # overrides environment variables
            help_styles = self._parse_colorspec(args.color)
            self.debug_msg("help styles set from --color")
        elif args.nocolor:
            # disable the default color output
            help_styles = self._parse_colorspec("")
            self.debug_msg("help styles disabled because of --no-color")
        elif env_no_color:
            help_styles = self._parse_colorspec("")
            self.debug_msg("disabling color output because NO_COLOR is set")
        elif env_colors == "":
            # None is different than an empty string
            # disable the default color output
            help_styles = self._parse_colorspec("")
            self.debug_msg(
                "no color output in help because $DYE_COLORS is an empty string"
            )
        elif env_colors:
            # was set, and was set to a non-empty string
            help_styles = self._parse_colorspec(env_colors)
            self.debug_msg("help styles set from $DYE_COLORS")
        else:
            self.debug_msg("no styles found for help")

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
        theme = self.load_theme_from_args(args, required=False)
        pattern = self.load_pattern_from_args(args, required=True, theme=theme)

        # if we got scope(s) on the command line, use them, otherwise we'll
        # apply all scopes
        to_apply = args.scope.split(",") if args.scope else list(pattern.scopes.keys())

        for scope_name in to_apply:
            # checking here in case they supplied a scope on the command line that
            # doesn't exist
            try:
                scope = pattern.scopes[scope_name]
            except KeyError as exc:
                raise DyeError(f"{scope_name}: no such scope") from exc
            scope.run_agent(args.comment)
        return self.EXIT_SUCCESS

    def command_preview(self, args):
        """Display a preview of the styles in a theme"""
        theme = self.load_theme_from_args(args, required=False)
        pattern = self.load_pattern_from_args(args, required=False, theme=theme)
        if not theme and not pattern:
            raise DyeError("nothing to preview")

        # the text style here makes the whole panel print with the foreground
        # and background colors from the style
        try:
            text_style = pattern.styles["text"]
        except KeyError as exc:
            raise DyeSyntaxError("no 'text' style defined") from exc

        outer_table = rich.table.Table(
            box=rich.box.ROUNDED,
            show_lines=True,
            expand=True,
            show_header=False,
            padding=0,
        )

        # output some basic information about the theme and pattern
        summary_table = rich.table.Table(
            box=None,
            expand=False,
            show_header=False,
            padding=(0, 0, 0, 1),
        )

        if theme:
            summary_table.add_row("Theme file:", theme.filename)
            theme_description = (
                f' = "{theme.description}"' if theme.description else " ="
            )
            summary_table.add_row("  description", theme_description)
            theme_type = f' = "{theme.type}"' if theme.type else " ="
            summary_table.add_row("  type", theme_type)
            theme_version = f' = "{theme.version}"' if theme.version else " ="
            summary_table.add_row("  version", theme_version)
        else:
            summary_table.add_row("No theme file.")
        summary_table.add_row("")

        if pattern:
            summary_table.add_row("Pattern file:", pattern.filename)
            pattern_description = (
                f' = "{pattern.description}"' if pattern.description else " ="
            )
            summary_table.add_row("  description", pattern_description)
            pattern_type = f' = "{pattern.type}"' if pattern.type else " ="
            summary_table.add_row("  type", pattern_type)
            pattern_version = f' = "{pattern.version}"' if pattern.version else " ="
            summary_table.add_row("  version", pattern_version)
        else:
            summary_table.add_row("No pattern file.")

        # add the summary table to the outer table
        outer_table.add_row(" Inputs")
        outer_table.add_row(summary_table)

        # add colors
        colors_table = rich.table.Table(
            box=None,
            expand=False,
            padding=(0, 0, 0, 1),
            style=text_style,
        )
        outer_table.add_row(" [colors]")
        outer_table.add_section()
        for color_name in pattern.colors.keypaths(sort=False):
            if isinstance(pattern.colors[color_name], dict):
                # this one is a nested table, skip it
                continue
            (source, color_def) = self.get_color_def(theme, pattern, color_name)
            col1 = rich.text.Text.assemble(("██", color_def), f" {color_name}")
            col2 = rich.text.Text(f' = "{color_def}"  # from {source}')
            colors_table.add_row(col1, col2)
        outer_table.add_row(colors_table)

        # add styles
        styles_table = rich.table.Table(
            box=None,
            expand=False,
            padding=(0, 0, 0, 1),
            style=text_style,
        )
        outer_table.add_row(" [styles]")
        outer_table.add_section()
        for style_name in pattern.styles.keypaths(sort=False):
            if isinstance(pattern.styles[style_name], dict):
                # this one is a nested table, skip it
                continue
            (source, style_def) = self.get_style_def(theme, pattern, style_name)
            style = pattern.styles[style_name]
            col1 = rich.text.Text(style_name, style)
            col2 = rich.text.Text(f' = "{style_def}"  # from {source}')
            styles_table.add_row(col1, col2)
        outer_table.add_row(styles_table)

        # print the whole thing out
        self.console.print(
            rich.panel.Panel(outer_table, box=rich.box.SIMPLE, style=text_style)
        )
        return self.EXIT_SUCCESS

    def get_color_def(self, theme, pattern, color_name):
        """retrieve the definition of color_name from theme or pattern

        Args:
            theme (Theme): _description_
            pattern (Pattern): _description_
            color_name (str): _description_
        """
        found = False
        source = None
        color_def = None

        with contextlib.suppress(KeyError):
            color_def = theme.definition["colors"][color_name]
            source = "theme"
            found = True
        with contextlib.suppress(KeyError):
            color_def = pattern.definition["colors"][color_name]
            source = "pattern"
            found = True

        if not found:
            raise KeyError(color_name)
        return (source, color_def)

    def get_style_def(self, theme, pattern, style_name):
        """retrieve the definition of style_name from theme or pattern

        Args:
            theme (Theme): _description_
            pattern (Pattern): _description_
            style_name (str): _description_
        """
        found = False
        source = None
        style_def = None

        with contextlib.suppress(KeyError):
            style_def = theme.definition["styles"][style_name]
            source = "theme"
            found = True
        with contextlib.suppress(KeyError):
            style_def = pattern.definition["styles"][style_name]
            source = "pattern"
            found = True
        if not found:
            raise KeyError(style_name)
        return (source, style_def)

    def command_print(self, args):
        """print arbitrary strings applying styles from a theme or pattern"""
        theme = self.load_theme_from_args(args, required=False)
        pattern = self.load_pattern_from_args(args, required=False, theme=theme)

        style = None
        if args.style:
            with contextlib.suppress(KeyError):
                style = pattern.styles[args.style]

        # build a rich.theme object from our styles
        rich_theme = rich.theme.Theme(pattern.styles)
        # and use it for just a moment
        with self.print_console.use_theme(rich_theme, inherit=False):
            if args.n:
                self.print_console.print(" ".join(args.string), style=style, end="")
            else:
                self.print_console.print(" ".join(args.string), style=style)
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
        if not self.dye_theme_dir:
            errmsg = (
                "the DYE_DIR environment variable must be set"
                " and that directory must contain a 'themes' directory"
            )
            raise DyeError(errmsg)
        if not self.dye_theme_dir.is_dir():
            errmsg = f"{self.dye_theme_dir}: is not a directory"
            raise DyeError(errmsg)

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

    def debug_msg(self, msg):
        """print the message to stderr if debug is enabled"""
        if self.debug:
            self.error_console.print(f"[debug] {msg}")

    def load_theme_from_args(self, args, required=True):
        """Load a theme from the command line args

        required - whether we have to have a theme file or not
                if required=False an empty theme can be returned

        Will raise an exception if args specify a file and it
        doesn't exist or can't be opened

        Resolution order:
        1. --themefile, -t from the command line
        2. $DYE_THEME_FILE environment variable

        This returns a theme object

        :raises: an exception if we can't find a theme file

        """
        if required and args.no_theme:
            raise DyeError("a theme is required and you specified --no-theme")

        if not required and args.no_theme:
            return Theme()

        fname = None

        if args.theme_file:
            fname = args.theme_file
        else:
            with contextlib.suppress(KeyError):
                fname = os.environ["DYE_THEME_FILE"]
                self.debug_msg(f"found theme '{fname}' in $DYE_THEME_FILE")

        if fname:
            with open(os.path.expanduser(fname), "rb") as file:
                self.debug_msg(f"loading theme from '{fname}'")
                theme = Theme.load(file, filename=fname)
            return theme

        if required:
            raise DyeError("no theme specified")

        self.debug_msg("no theme specified")
        return Theme()

    def load_pattern_from_args(self, args, required=True, theme=None):
        """load a pattern file from the args

        Resolution order:
        1. --patternfile -f from the command line
        2. $DYE_PATTERN_FILE environment variable

        This returns a pattern object

        :raises: an exception if we can't find a pattern file

        It's up to the caller to match up the required parameters and the
        args in the namespace. If you pass required=False, this will check for
        args.no_pattern and ignore the environment variable and args.pattern_file
        """
        # if we don't have a no_pattern attribute, make sure it's set to false
        # some versions of the args we call with (like those for apply), don't
        # have this argument because it doesn't make any sense
        if not hasattr(args, "no_pattern"):
            args.no_pattern = False

        if required and args.no_pattern:
            raise DyeError("a pattern is required and you specified --no-pattern")

        if not required and args.no_pattern:
            return Pattern.loads(None, theme)

        fname = None

        if args.pattern_file:
            fname = args.pattern_file
        else:
            with contextlib.suppress(KeyError):
                fname = os.environ["DYE_PATTERN_FILE"]
                self.debug_msg(f"found pattern '{fname}' in $DYE_PATTERN_FILE")

        if fname:
            with open(os.path.expanduser(fname), "rb") as fobj:
                self.debug_msg(f"loading pattern from '{fname}'")
                pattern = Pattern.load(fobj, theme, filename=fname)
            return pattern

        if required:
            raise DyeError("no pattern specified")

        self.debug_msg("no pattern specified")
        return Pattern()

    #
    # static methods for running from the command line
    # main() below is called from src/dye/__main__.py
    #
    @staticmethod
    def main(argv=None):
        """Entry point from the command line

        parse arguments and call dispatch() for processing
        """

        parser = Dye.argparser()
        try:
            args = parser.parse_args(argv)
        except SystemExit as exc:
            return exc.code

        # create an instance of ourselves
        thm = Dye(force_color=args.force_color)
        return thm.dispatch(parser.prog, args)

    @staticmethod
    def argparser():
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
        parser.add_argument(
            "-F", "--force-color", action="store_true", help=forcecolor_help
        )

        # debug
        debug_help = "output debug and status information to stderr"
        parser.add_argument("-d", "--debug", action="store_true", help=debug_help)

        # set up for the sub commands
        subparsers = parser.add_subparsers(
            dest="command",
            title="arguments",
            metavar="<command>",
            required=False,
            help="command to perform, which must be one of the following:",
        )

        Dye._argparser_apply(subparsers)
        Dye._argparser_preview(subparsers)
        Dye._argparser_print(subparsers)
        Dye._argparser_agents(subparsers)
        Dye._argparser_themes(subparsers)
        Dye._argparser_help(subparsers)

        return parser

    @staticmethod
    def _argparser_apply(subparsers):
        # apply command
        cmdhelp = "apply a theme"
        parser = subparsers.add_parser(
            "apply",
            description=cmdhelp,
            formatter_class=RichHelpFormatter,
            help=cmdhelp,
        )
        pfile_help = "specify a file containing a pattern"
        parser.add_argument("-f", "--pattern-file", metavar="<path>", help=pfile_help)

        theme_group = parser.add_mutually_exclusive_group()
        tfile_help = "specify a file containing a theme"
        theme_group.add_argument(
            "-t", "--theme-file", metavar="<path>", help=tfile_help
        )
        no_theme_help = "don't load any theme, ignores DYE_THEME_FILE"
        theme_group.add_argument("--no-theme", action="store_true", help=no_theme_help)

        scope_help = "only apply the given scope"
        parser.add_argument("-s", "--scope", help=scope_help)
        comment_help = "add comments to the generated shell output"
        parser.add_argument("-c", "--comment", action="store_true", help=comment_help)

    @staticmethod
    def _argparser_preview(subparsers):
        """Add a subparser for the preview command"""
        cmd_help = "show a preview of the styles in a theme"
        parser = subparsers.add_parser(
            "preview",
            description=cmd_help,
            formatter_class=RichHelpFormatter,
            help=cmd_help,
        )
        pattern_group = parser.add_mutually_exclusive_group()
        pfile_help = "specify a file containing a pattern"
        pattern_group.add_argument(
            "-f", "--pattern-file", metavar="<path>", help=pfile_help
        )
        no_pattern_help = "don't load any pattern, ignores DYE_PATTERN_FILE"
        pattern_group.add_argument(
            "--no-pattern", action="store_true", help=no_pattern_help
        )

        theme_group = parser.add_mutually_exclusive_group()
        tfile_help = "specify a file containing a theme"
        theme_group.add_argument(
            "-t", "--theme-file", metavar="<path>", help=tfile_help
        )
        no_theme_help = "don't load any theme, ignores DYE_THEME_FILE"
        theme_group.add_argument("--no-theme", action="store_true", help=no_theme_help)

    @staticmethod
    def _argparser_print(subparsers):
        """Add a subparser for the print command"""
        desc = """
            Print text using styles from a theme or pattern.
            String arguments are printed, seperated by a space, and followed
            by a newline character, to standard output.
        """
        # desc = textwrap.dedent(desc)
        parser = subparsers.add_parser(
            "print",
            description=desc,
            formatter_class=RichHelpFormatter,
            help="print text using styles from a theme or pattern",
        )
        newline_help = "do not append a newline"
        parser.add_argument("-n", action="store_true", help=newline_help)

        pattern_group = parser.add_mutually_exclusive_group()
        pfile_help = "specify a file containing a pattern"
        pattern_group.add_argument(
            "-f", "--pattern-file", metavar="<path>", help=pfile_help
        )
        no_pattern_help = "don't load any pattern, ignores DYE_PATTERN_FILE"
        pattern_group.add_argument(
            "--no-pattern", action="store_true", help=no_pattern_help
        )

        theme_group = parser.add_mutually_exclusive_group()
        tfile_help = "specify a file containing a theme"
        theme_group.add_argument(
            "-t", "--theme-file", metavar="<path>", help=tfile_help
        )
        no_theme_help = "don't load any theme, ignores DYE_THEME_FILE"
        theme_group.add_argument("--no-theme", action="store_true", help=no_theme_help)

        style_help = "apply this style to the output"
        parser.add_argument("-s", "--style", metavar="<style>", help=style_help)

        string_help = "strings to be printed"
        parser.add_argument("string", nargs="*", help=string_help)

    @staticmethod
    def _argparser_agents(subparsers):
        """Add a subparser for the agents command"""
        # agents command
        agents_help = "list all known agents"
        subparsers.add_parser(
            "agents",
            description=agents_help,
            formatter_class=RichHelpFormatter,
            help=agents_help,
        )

    @staticmethod
    def _argparser_themes(subparsers):
        """Add a subparser for the themes command"""
        themes_help = "list available themes"
        subparsers.add_parser(
            "themes",
            description=themes_help,
            formatter_class=RichHelpFormatter,
            help=themes_help,
        )

    @staticmethod
    def _argparser_help(subparsers):
        """Add a subparser for the help command"""
        help_help = "display this usage message"
        subparsers.add_parser(
            "help",
            description=help_help,
            formatter_class=RichHelpFormatter,
            help=help_help,
        )
