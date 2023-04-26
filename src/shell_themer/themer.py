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
"""command line tool for maintaining and switching color schemes"""

import argparse
import functools
import os
import pathlib
import re
import subprocess
import sys


import rich.box
import rich.color
import rich.console
import rich.errors
import rich.layout
import rich.style
from rich_argparse import RichHelpFormatter
import tomlkit

from .version import version_string


class Themer:
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

        # the path to the theme file if we loaded from a file
        # note that this can be None even with a valid loaded theme
        # because of self.loads()
        self.theme_file = None
        self.definition = {}
        self.styles = {}

        self.loads()

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
            try:
                fname = pathlib.Path(os.environ["THEME_FILE"])
            except KeyError:
                pass
        if not fname:
            raise ThemeError(f"{self.prog}: no theme or theme file specified")

        with open(fname, "rb") as file:
            self.definition = tomlkit.load(file)
        self.theme_file = fname
        self._process_definition()

    def loads(self, tomlstring=None):
        """Load a theme from a given string"""
        if tomlstring:
            toparse = tomlstring
        else:
            # tomlkit can't parse None, so if we got it as the default
            # or if the caller pased None intentionally...
            toparse = ""
        self.definition = tomlkit.loads(toparse)
        self._process_definition()

    def _process_definition(self):
        """process a newly loaded definition, including variables and styles"""

        # process the styles
        self.styles = {}
        try:
            for key, styledef in self.definition["styles"].items():
                # interpolate variables
                interpdef = self.variable_interpolate(styledef)
                # and parse the style definition
                self.styles[key] = rich.style.Style.parse(interpdef)
        except KeyError:
            pass

    #
    # style and variable related methods
    #
    def styles_from(self, scopedef):
        "Extract a dict of all the styles present in the given scope definition"
        styles = {}
        try:
            raw_styles = scopedef["style"]
            for key, value in raw_styles.items():
                styles[key] = self.get_style(value)
        except KeyError:
            pass
        return styles

    def get_style(self, styledef):
        """convert a string into rich.style.Style object"""
        # first check if this definition is already in our list of styles
        try:
            style = self.styles[styledef]
        except KeyError:
            style = None
        # nope, parse the input as a style
        if not style:
            interp = self.variable_interpolate(styledef)
            style = rich.style.Style.parse(interp)
        return style

    def value_of(self, variable):
        """return the value or contents of a variable
        performs variable interpolation at access time, not at
        parse time
        return None if variable is not defined"""

        variables = {}
        try:
            variables = self.definition["variables"]
            definedvalue = variables[variable]
            # we can only interpolate variables in string type values
            if isinstance(definedvalue, str):
                value = self.variable_interpolate(definedvalue)
                return self.style_interpolate(value)
            return definedvalue
        except KeyError:
            # variable not defined
            return None

    def variable_interpolate(self, value):
        """interpolate variables in the passed value"""
        # this incantation gives us a callable function which is
        # really a method on our class, and which gets self
        # passed to the method just like any other method
        tmpfunc = functools.partial(self._var_subber)
        # this regex matches any of the following:
        #   {var:darkorange}
        #   {variable:yellow}
        #   \{variable:blue}
        # so we can replace it with a previously defined variable.
        #
        # match group 1 = backslash, if present
        # match group 2 = entire variable phrase
        # match group 3 = 'var' or 'variable'
        # match group 4 = name of the variable
        newvalue = re.sub(
            r"(\\)?(\{(var|variable):([^}:]*)(?::(.*))?\})", tmpfunc, value
        )
        return newvalue

    def _var_subber(self, match):
        """the replacement function called by re.sub() in variable_interpolate()

        this decides the replacement text for the matched regular expression

        the philosophy is to have the replacement string be exactly what was
        matched in the string, unless we the variable given exists and has a
        value, in which case we insert that value.
        """
        # the backslash to protect the brace, may or may not be present
        backslash = match.group(1)
        # the entire phrase, including the braces
        phrase = match.group(2)
        # match.group(3) is the literal 'var' or 'variable', we don't need that
        # the stuff after the colon but before the closing brace
        varname = match.group(4)

        if backslash:
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            out = f"{phrase}"
        else:
            value = self.value_of(varname)
            if value is None:
                # we can't find the variable, so don't do a replacement
                out = match.group(0)
            else:
                if isinstance(value, bool):
                    # toml booleans are all lower case, python are not
                    # since the source toml is all lower case, we will
                    # make the replacement be the same
                    out = str(value).lower()
                else:
                    out = str(value)
        return out

    def style_interpolate(self, value):
        """interpolate styles in a passed value"""
        # this incantation gives us a callable function which is
        # really a method on our class, and which gets self
        # passed to the method just like any other method
        tmpfunc = functools.partial(self._style_subber)
        # this regex matches any of the following:
        #   {style:darkorange}
        #   {style:yellow:}
        #   \{style:blue:hex}
        # so we can replace it with style information.
        #
        # match group 1 = backslash, if present
        # match group 2 = entire style/format phrase
        # match group 3 = name of the style (not the literal 'style:')
        # match group 4 = format
        newvalue = re.sub(r"(\\)?(\{style:([^}:]*)(?::(.*))?\})", tmpfunc, value)
        return newvalue

    def _style_subber(self, match):
        """the replacement function called by re.sub()

        this decides the replacement text for the matched regular expression

        the philosophy is to have the replacement string be exactly what was
        matched in the string, unless we can successfully decode both the
        style and the format.
        """
        # the backslash to protect the brace, may or may not be present
        backslash = match.group(1)
        # the entire phrase, including the braces
        phrase = match.group(2)
        # the stuff after the opening brace but before the colon
        # this is the defition of the style
        styledef = match.group(3)
        # the stuff after the colon but before the closing brace
        fmt = match.group(4)

        if backslash:
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            out = f"{phrase}"
        else:
            try:
                style = self.get_style(styledef)
            except rich.errors.StyleSyntaxError:
                style = None

            if not style:
                # the style wasn't found, so don't do any replacement
                out = match.group(0)
            elif fmt in [None, "", "hex"]:
                # no format, or empty string format, or hex, the match with the hex code
                out = style.color.triplet.hex
            elif fmt == "hexnohash":
                # replace the match with the hex code without the hash
                out = style.color.triplet.hex.replace("#", "")
            else:
                # unknown format, so don't do any replacement
                out = phrase

        return out

    #
    # scope, parsing, and validation methods
    #
    def has_scope(self, scope):
        """Check if the given scope exists."""
        try:
            _ = self.definition["scope"][scope]
            return True
        except KeyError:
            return False

    def scopedef_for(self, scope):
        "Extract all the data for a given scope, or an empty dict if there is none"
        scopedef = {}
        try:
            scopedef = self.definition["scope"][scope]
        except KeyError:
            # scope doesn't exist
            pass
        return scopedef

    def is_enabled(self, scope):
        """Determine if the scope is enabled
        The default is that the scope is enabled

        If can be disabled by:

            enabled = false

        or:
            enabled_if = "{shell cmd}" returns a non-zero exit code

        if 'enabled = false' is present, then enabled_if is not checked
        """
        scopedef = self.scopedef_for(scope)
        try:
            enabled = scopedef["enabled"]
            self._assert_bool(enabled, None, scope, "enabled")
            # this is authoritative, if it exists, ignore enabled_if below
            return enabled
        except KeyError:
            # no enabled command, but we need to still keep checking
            pass

        try:
            enabled_if = scopedef["enabled_if"]
            if not enabled_if:
                # no command, by rule we say it's enabled
                return True
        except KeyError:
            # no enabled_if command, so we must be enabled
            return True

        enabled_if = self.variable_interpolate(enabled_if)
        enabled_if = self.style_interpolate(enabled_if)
        proc = subprocess.run(enabled_if, shell=True, check=False, capture_output=True)
        if proc.returncode != 0:
            # the shell command returned a non-zero exit code
            # and this scope should therefore be disabled
            return False
        return True

    def _assert_bool(self, value, generator, scope, key):
        if not isinstance(value, bool):
            if generator:
                errmsg = (
                    f"{self.prog}: {generator} generator for"
                    f" scope '{scope}' requires '{key}' to be true or false"
                )
            else:
                errmsg = (
                    f"{self.prog}: scope '{scope}' requires '{key}' to be true or false"
                )
            raise ThemeError(errmsg)

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

        mystyles = self.styles.copy()
        try:
            text_style = mystyles["text"]
        except KeyError:
            # if they didn't specify a text style, tell Rich to just use
            # whatever the default is for the terminal
            text_style = "default"
        try:
            del mystyles["background"]
        except KeyError:
            pass

        outer_table = rich.table.Table(
            box=rich.box.SIMPLE_HEAD, expand=True, show_header=False
        )

        summary_table = rich.table.Table(box=None, expand=True, show_header=False)
        summary_table.add_row("Theme file:", str(self.theme_file))
        try:
            name = self.definition["name"]
        except KeyError:
            name = ""
        summary_table.add_row("Name:", name)
        try:
            version = self.definition["version"]
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
            for name, scopedef in self.definition["scope"].items():
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
                for scope in self.definition["scope"].keys():
                    to_generate.append(scope)
            except KeyError:
                pass

        for scope in to_generate:
            # checking here in case they supplied a scope on the command line that
            # doesn't exist
            if self.has_scope(scope):
                scopedef = self.scopedef_for(scope)
                # find the generator for this scope
                try:
                    generator = scopedef["generator"]
                except KeyError as exc:
                    errmsg = f"{self.prog}: scope '{scope}' does not have a generator defined"
                    raise ThemeError(errmsg) from exc
                # check if the scope is disabled
                if not self.is_enabled(scope):
                    if args.comment:
                        print(f"# [scope.{scope}] skipped because it is not enabled")
                    continue
                # scope is enabled, so print the comment
                if args.comment:
                    print(f"# [scope.{scope}]")

                if generator == "environment_variables":
                    self._generate_environment(scope, scopedef)
                elif generator == "fzf":
                    self._generate_fzf(scope, scopedef)
                elif generator == "ls_colors":
                    self._generate_ls_colors(scope, scopedef)
                elif generator == "exa_colors":
                    self._generate_exa_colors(scope, scopedef)
                elif generator == "iterm":
                    self._generate_iterm(scope, scopedef)
                elif generator == "shell":
                    self._generate_shell(scope, scopedef)
                else:
                    raise ThemeError(f"{self.prog}: {generator}: unknown generator")
            else:
                raise ThemeError(f"{self.prog}: {scope}: no such scope")
        return self.EXIT_SUCCESS

    #
    # environment generator
    #
    def _generate_environment(self, _, scopedef):
        """Render environment variables from a set of attributes and styles"""
        # render the variables to unset
        try:
            unsets = scopedef["environment"]["unset"]
            if isinstance(unsets, str):
                # if they used a string in the config file instead of a list
                # process it like a single item instead of trying to process
                # each letter in the string
                unsets = [unsets]
            for unset in unsets:
                print(f"unset {unset}")
        except KeyError:
            pass
        # render the variables to export
        try:
            exports = scopedef["environment"]["export"]
            for var, value in exports.items():
                value = self.variable_interpolate(value)
                value = self.style_interpolate(value)
                print(f'export {var}="{value}"')
        except KeyError:
            pass

    #
    # fzf generator and helpers
    #
    def _generate_fzf(self, scope, scopedef):
        """render attribs into a shell statement to set an environment variable"""
        optstr = ""

        # process all the command line options
        try:
            opts = scopedef["opt"]
        except KeyError:
            opts = {}

        for key, value in opts.items():
            if isinstance(value, str):
                interp_value = self.variable_interpolate(value)
                optstr += f" {key}='{interp_value}'"
            elif isinstance(value, bool) and value:
                optstr += f" {key}"

        # process all the styles
        colors = []
        # then add them back
        for name, style in self.styles_from(scopedef).items():
            colors.append(self._fzf_from_style(name, style))
        # turn off all the colors, and add our color strings
        try:
            colorbase = f"{scopedef['colorbase']},"
        except KeyError:
            colorbase = ""
        if colorbase or colors:
            colorstr = f" --color='{colorbase}{','.join(colors)}'"
        else:
            colorstr = ""

        # figure out which environment variable to put it in
        try:
            varname = scopedef["environment_variable"]
            varname = self.variable_interpolate(varname)
            print(f'export {varname}="{optstr}{colorstr}"')
        except KeyError as exc:
            raise ThemeError(
                (
                    f"{self.prog}: fzf generator requires 'environment_variable'"
                    f" key to process scope '{scope}'"
                )
            ) from exc

    def _fzf_from_style(self, name, style):
        """turn a rich.style into a valid fzf color"""
        fzf = []
        if name == "text":
            # turn this into fg and bg color names
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf.append(f"fg:{fzfc}:{fzfa}")
            if style.bgcolor:
                fzfc = self._fzf_color_from_rich_color(style.bgcolor)
                fzf.append(f"bg:{fzfc}")
        elif name == "current_line":
            # turn this into fg+ and bg+ color names
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf.append(f"fg+:{fzfc}:{fzfa}")
            if style.bgcolor:
                fzfc = self._fzf_color_from_rich_color(style.bgcolor)
                fzf.append(f"bg+:{fzfc}")
        elif name == "preview":
            # turn this into fg+ and bg+ color names
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf.append(f"preview-fg:{fzfc}:{fzfa}")
            if style.bgcolor:
                fzfc = self._fzf_color_from_rich_color(style.bgcolor)
                fzf.append(f"preview-bg:{fzfc}")
        else:
            # we only use the foreground color of the style, and ignore
            # any background color specified by the style
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf.append(f"{name}:{fzfc}:{fzfa}")

        return ",".join(fzf)

    def _fzf_color_from_rich_color(self, color):
        """turn a rich.color into it's fzf equivilent"""
        fzf = ""

        if color.type == rich.color.ColorType.DEFAULT:
            fzf = "-1"
        elif color.type == rich.color.ColorType.STANDARD:
            # python rich uses underscores, fzf uses dashes
            fzf = str(color.number)
        elif color.type == rich.color.ColorType.EIGHT_BIT:
            fzf = str(color.number)
        elif color.type == rich.color.ColorType.TRUECOLOR:
            fzf = color.triplet.hex
        return fzf

    def _fzf_attribs_from_style(self, style):
        attribs = "regular"
        if style.bold:
            attribs += ":bold"
        if style.underline:
            attribs += ":underline"
        if style.reverse:
            attribs += ":reverse"
        if style.dim:
            attribs += ":dim"
        if style.italic:
            attribs += ":italic"
        if style.strike:
            attribs += ":strikethrough"
        return attribs

    #
    # ls_colors generator
    #
    LS_COLORS_BASE_MAP = {
        # map both a friendly name and the "real" name
        "text": "no",
        "file": "fi",
        "directory": "di",
        "symlink": "ln",
        "multi_hard_link": "mh",
        "pipe": "pi",
        "socket": "so",
        "door": "do",
        "block_device": "bd",
        "character_device": "cd",
        "broken_symlink": "or",
        "missing_symlink_target": "mi",
        "setuid": "su",
        "setgid": "sg",
        "sticky": "st",
        "other_writable": "ow",
        "sticky_other_writable": "tw",
        "executable_file": "ex",
        "file_with_capability": "ca",
    }
    # this map allows you to either use the 'native' color code, or the
    # 'friendly' name defined by shell-themer
    LS_COLORS_MAP = {}
    for friendly, actual in LS_COLORS_BASE_MAP.items():
        LS_COLORS_MAP[friendly] = actual
        LS_COLORS_MAP[actual] = actual

    def _generate_ls_colors(self, scope, scopedef):
        "Render a LS_COLORS variable suitable for GNU ls"
        outlist = []
        havecodes = []
        # process the styles
        styles = self.styles_from(scopedef)
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = scopedef["clear_builtin"]
            self._assert_bool(clear_builtin, "ls_colors", scope, "clear_builtin")
        except KeyError:
            clear_builtin = False

        # iterate over the styles given in our configuration
        for name, style in styles.items():
            if style:
                mapcode, render = self._ls_colors_from_style(
                    name, style, self.LS_COLORS_MAP, scope
                )
                havecodes.append(mapcode)
                outlist.append(render)

        if clear_builtin:
            style = self.get_style("default")
            # go through all the color codes, and render them with the
            # 'default' style and add them to the output
            for name, code in self.LS_COLORS_BASE_MAP.items():
                if not code in havecodes:
                    _, render = self._ls_colors_from_style(
                        name, style, self.LS_COLORS_MAP, scope
                    )
                    outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = scopedef["environment_variable"]
            varname = self.variable_interpolate(varname)
        except KeyError:
            varname = "LS_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        print(f'''export {varname}="{':'.join(outlist)}"''')

    def _ls_colors_from_style(self, name, style, mapp, scope):
        """create an entry suitable for LS_COLORS from a style

        name should be a valid LS_COLORS entry, could be a code representing
        a file type, or a glob representing a file extension

        style is a style object

        mapp is a dictionary of friendly color names to native color names
            ie map['directory'] = 'di'

        scope is the scope where this mapped occured, used for error message
        """
        ansicodes = ""
        if not style:
            return "", ""
        try:
            mapname = mapp[name]
        except KeyError as exc:
            # they used a style for a file attribute that we don't know how to map
            # i.e. style.text or style.directory we know what to do with, but
            # style.bundleid we don't know how to map, so we generate an error
            raise ThemeError(
                (
                    f"{self.prog}: unknown style '{name}' while processing"
                    f" scope '{scope}' using the 'ls_colors' generator"
                )
            ) from exc

        if style.color.type == rich.color.ColorType.DEFAULT:
            ansicodes = "0"
        else:
            # this works, but it uses a protected method
            #   ansicodes = style._make_ansi_codes(rich.color.ColorSystem.TRUECOLOR)
            # here's another approach, we ask the style to render a string, then
            # go peel the ansi codes out of the generated escape sequence
            ansistring = style.render("-----")
            # style.render uses this string to build it's output
            # f"\x1b[{attrs}m{text}\x1b[0m"
            # so let's go split it apart
            match = re.match(r"^\x1b\[([;\d]*)m", ansistring)
            # and get the numeric codes
            ansicodes = match.group(1)
        return mapname, f"{mapname}={ansicodes}"

    #
    # exa color generator
    #
    EXA_COLORS_BASE_MAP = {
        # map both a friendly name and the "real" name
        "text": "no",
        "file": "fi",
        "directory": "di",
        "symlink": "ln",
        "multi_hard_link": "mh",
        "pipe": "pi",
        "socket": "so",
        "door": "do",
        "block_device": "bd",
        "character_device": "cd",
        "broken_symlink": "or",
        "missing_symlink_target": "mi",
        "setuid": "su",
        "setgid": "sg",
        "sticky": "st",
        "other_writable": "ow",
        "sticky_other_writable": "tw",
        "executable_file": "ex",
        "file_with_capability": "ca",
        "perms_user_read": "ur",
        "perms_user_write": "uw",
        "perms_user_execute_files": "ux",
        "perms_user_execute_directories": "ue",
        "perms_group_read": "gr",
        "perms_group_write": "gw",
        "perms_group_execute": "gx",
        "perms_other_read": "tr",
        "perms_other_write": "tw",
        "perms_other_execute": "tx",
        "perms_suid_files": "su",
        "perms_sticky_directories": "sf",
        "perms_extended_attribute": "xa",
        "size_number": "sn",
        "size_unit": "sb",
        "df": "df",
        "ds": "ds",
        "uu": "uu",
        "un": "un",
        "gu": "gu",
        "gn": "gn",
        "lc": "lc",
        "lm": "lm",
        "ga": "ga",
        "gm": "gm",
        "gd": "gd",
        "gv": "gv",
        "gt": "gt",
        "punctuation": "xx",
        "date_time": "da",
        "in": "in",
        "bl": "bl",
        "column_headers": "hd",
        "lp": "lp",
        "cc": "cc",
        "b0": "b0",
    }
    # this map allows you to either use the 'native' exa code, or the
    # 'friendly' name defined by shell-themer
    EXA_COLORS_MAP = {}
    for friendly, actual in EXA_COLORS_BASE_MAP.items():
        EXA_COLORS_MAP[friendly] = actual
        EXA_COLORS_MAP[actual] = actual

    def _generate_exa_colors(self, scope, scopedef):
        "Render a EXA_COLORS variable suitable for exa"
        outlist = []
        # process the styles
        styles = self.styles_from(scopedef)
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = scopedef["clear_builtin"]
            self._assert_bool(clear_builtin, "exa_colors", scope, "clear_builtin")
        except KeyError:
            clear_builtin = False

        if clear_builtin:
            # this tells exa to not use any built-in/hardcoded colors
            outlist.append("reset")

        # iterate over the styles given in our configuration
        for name, style in styles.items():
            if style:
                _, render = self._ls_colors_from_style(
                    name, style, self.EXA_COLORS_MAP, scope
                )
                outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = scopedef["environment_variable"]
            varname = self.variable_interpolate(varname)
        except KeyError:
            varname = "EXA_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        print(f'''export {varname}="{':'.join(outlist)}"''')

    #
    # iterm generator and helpers
    #
    def _generate_iterm(self, _, scopedef):
        """send the special escape sequences to make the iterm2
        terminal emulator for macos change its foreground and backgroud
        color

        echo "\033]1337;SetColors=bg=331111\007"
        """
        styles = self.styles_from(scopedef)
        self._iterm_render_style(styles, "foreground", "fg")
        self._iterm_render_style(styles, "background", "bg")

    def _iterm_render_style(self, styles, style_name, iterm_key):
        """print an iterm escape sequence to change the color palette"""
        try:
            style = styles[style_name]
        except KeyError:
            return
        if style:
            clr = style.color.get_truecolor()
            # gotta use raw strings here so the \033 and \007 don't get
            # interpreted by python
            out = r'builtin echo -e "\e]1337;'
            out += f"SetColors={iterm_key}={clr.hex.replace('#','')}"
            out += r'\a"'
            print(out)

    #
    # shell command generator
    #
    def _generate_shell(self, _, scopedef):
        try:
            cmds = scopedef["command"]
            for _, cmd in cmds.items():
                cmd = self.variable_interpolate(cmd)
                cmd = self.style_interpolate(cmd)
                print(cmd)
        except KeyError:
            pass


class ThemeError(Exception):
    """Exception for theme processing errors"""
