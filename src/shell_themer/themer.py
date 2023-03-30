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

import functools
import os
import pathlib
import re
import subprocess

import rich.box
import rich.color
import rich.console
import rich.errors
import rich.layout
import rich.style
import tomlkit


class Themer:
    """parse and translate a theme file for various command line programs"""

    EXIT_SUCCESS = 0
    EXIT_ERROR = 1

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

    def load_from_args(self, args):
        """Load a theme from the command line args

        Resolution order:
        1. --file from the command line
        2. --theme from the command line
        3. $THEME_FILE environment variable

        This either loads the theme or raises an exception.
        It doesn't return anything

        :raises: ThemeError if we can't find a theme file

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
        self._parse_styles()

    def loads(self, tomlstring=None):
        """Load a theme from a given string"""
        if tomlstring:
            toparse = tomlstring
        else:
            # tomlkit can't parse None, so if we got it as the default
            # or if the caller pased None intentionally...
            toparse = ""
        self.definition = tomlkit.loads(toparse)
        self._parse_styles()

    #
    # style related methods
    #
    def _parse_styles(self):
        """parse the styles section of the theme and put it into self.styles dict"""
        self.styles = {}
        try:
            for key, value in self.definition["styles"].items():
                self.styles[key] = rich.style.Style.parse(value)
        except KeyError:
            pass

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
            style = rich.style.Style.parse(styledef)
        return style

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
            self._assert_bool(None, scope, "enabled", enabled)
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

        proc = subprocess.run(enabled_if, shell=True, check=False, capture_output=True)
        if proc.returncode != 0:
            # the shell command returned a non-zero exit code
            # and this scope should therefore be disablee
            return False
        return True

    def _assert_bool(self, generator, scope, key, value):
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
    def dispatch(self, args):
        """Figure out which subcommand to run based on the arguments provided"""
        try:
            if args.command == "themes":
                return self.dispatch_themes(args)
            elif args.command == "preview":
                return self.dispatch_preview(args)
            elif args.command == "generate":
                return self.dispatch_generate(args)
        except ThemeError as err:
            self.error_console.print(err)
            return self.EXIT_ERROR

        # if we get here, we didn't know the command
        print(f"{self.prog}: {args.command}: unknown command")
        return self.EXIT_ERROR

    def dispatch_themes(self, args):
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
            text_style = None
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
        except KeyError:
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
            if self.has_scope(scope):
                scopedef = self.scopedef_for(scope)
                # check if the scope is disabled
                if not self.is_enabled(scope):
                    if args.comment:
                        print(f"# [scope.{scope}] skipped because it is not enabled")
                    continue
                # do the rendering elements for all scopes
                if args.comment:
                    print(f"# [scope.{scope}]")
                self._generate_environment(scope, scopedef)
                # see if we have a generator defined for custom rendering
                try:
                    generator = scopedef["generator"]
                except KeyError:
                    # no more to do for this scope, skip to the next iteration
                    # of the loop
                    continue

                if generator == "fzf":
                    self._generate_fzf(scope, scopedef)
                elif generator == "ls_colors":
                    self._generate_ls_colors(scope, scopedef)
                elif generator == "iterm":
                    self._generate_iterm(scope, scopedef)
                else:
                    # unknown generator specified in the scope
                    # definition. by rule, this is not an error,
                    # but you don't get any special rendering
                    pass
            else:
                raise ThemeError(f"{self.prog}: {scope}: no such scope")
        return self.EXIT_SUCCESS

    #
    # environment generator
    #
    def _generate_environment(self, scope, scopedef):
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
                interpolated_value = self._environment_interpolate(value)
                print(f'export {var}="{interpolated_value}"')
        except KeyError:
            pass

    def _environment_interpolate(self, value):
        """interpolate"""
        # this incantation gives us a callable function which is
        # really a method on our class, and which gets self
        # passed to the method just like any other method
        tmpfunc = functools.partial(self._env_subber)
        # this regex matches any of the following:
        #   {darkorange}
        #   {yellow:}
        #   {blue:format}
        # so we can replace it with style information. It also matches
        #   \{something}
        # so we can ignore it but get rid of the backslash
        #
        # match group 1 = backslash, if present
        # match group 2 = entire style/format phrase
        # match group 3 = style
        # match group 4 = format
        newvalue = re.sub(r"(\\)?(\{([^}:]*)(?::(.*))?\})", tmpfunc, value)
        return newvalue

    def _env_subber(self, match):
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
                optstr += f" {key}='{value}'"
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
            # no special processing for foreground and background
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf.append(f"{name}:{fzfc}:{fzfa}")

        return ",".join(fzf)

    def _fzf_color_from_rich_color(self, color):
        """turn a rich.color into it's fzf equivilent"""
        fzf = ""
        if not color:
            return fzf

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
    LS_COLORS_MAP = {
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

    def _generate_ls_colors(self, scope, scopedef):
        "Render a LS_COLORS variable suitable for GNU ls"
        outlist = []
        # process the styles
        styles = self.styles_from(scopedef)
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = scopedef["clear_builtin"]
            self._assert_bool("ls_colors", scope, "clear_builtin", clear_builtin)
        except KeyError:
            clear_builtin = False

        if clear_builtin:
            # iterate over all known styles
            for name in self.LS_COLORS_MAP:
                try:
                    style = styles[name]
                except KeyError:
                    # style isn't in our configuration, so put the default one in
                    style = self.get_style("default")
                if style:
                    outlist.append(self._ls_colors_from_style(name, style))
        else:
            # iterate over the styles given in our configuration
            for name, style in styles.items():
                if style:
                    outlist.append(self._ls_colors_from_style(name, style))

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = scopedef["environment_variable"]
        except KeyError:
            varname = "LS_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        print(f'''export {varname}="{':'.join(outlist)}"''')

    def _ls_colors_from_style(self, name, style):
        """create an entry suitable for LS_COLORS from a style

        name should be a valid LS_COLORS entry, could be a code representing
        a file type, or a glob representing a file extension

        style is a style object
        """
        ansicodes = ""
        if not style:
            # TODO validate this is what we actually want
            return ""
        try:
            mapname = self.LS_COLORS_MAP[name]
        except KeyError:
            # TODO validate this is what we actually want
            # probably we raise an exception
            return ""

        if style.color.type == rich.color.ColorType.DEFAULT:
            ansicodes = "0"
        else:
            # this works, but it uses a protected method
            # ansicodes = style._make_ansi_codes(rich.color.ColorSystem.TRUECOLOR)
            # here's another approach, we ask the style to render a string, then
            # go peel the ansi codes out of the generated escape sequence
            ansistring = style.render("-----")
            # style.render uses this string to build it's output
            # f"\x1b[{attrs}m{text}\x1b[0m"
            # so let's go split it apart
            match = re.match(r"^\x1b\[([;\d]*)m", ansistring)
            # and get the numeric codes
            ansicodes = match.group(1)
        return f"{mapname}={ansicodes}"

    #
    # iterm generator and helpers
    #
    def _generate_iterm(self, scope, scopedef):
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


# def my_repl_func(match):
#     """callback function"""
#     styledef = match.group(1)
#     fmt = match.group(2)
#     return f"{fmt}|{styledef}"

# def new_repl_func(match, selff=None):
#     """another callback function"""
#     return f"{selff.theme_dir}:{match.group(0)}"


class ThemeError(Exception):
    """Exception for theme processing errors"""
