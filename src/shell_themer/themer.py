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
import tomlkit
import os
import pathlib
import re
import sys

import rich.color
import rich.console
import rich.style


class Themer:
    """parse and translate a theme file for various command line programs"""

    EXIT_SUCCESS = 0
    EXIT_ERROR = 1

    def __init__(self, prog, error_console=None):
        """Construct a new Themer object

        console
        """

        self.prog = prog
        if error_console:
            self.error_console = error_console
        else:
            self.error_console = rich.console.Console(
                stderr=True,
                soft_wrap=True,
                markup=False,
                emoji=False,
                highlight=False,
            )

        self.definition = {}
        self.styles = {}

        self.loads()

    def load(self, theme_file=None):
        """Load a theme from a file

        :raises:

        """
        if theme_file:
            fname = theme_file
        else:
            try:
                fname = pathlib.Path(os.environ["THEME_FILE"])
            except KeyError:
                self.error_console.print(f"{self.prog}: $THEME_FILE not set")
                sys.exit(self.EXIT_ERROR)

        with open(fname, "rb") as file:
            self.definition = tomlkit.load(file)

        self._parse_styles()

    def loads(self, tomlstring=None):
        """Load a theme from a given string"""
        if tomlstring:
            toparse = tomlstring
        else:
            toparse = ""
        self.definition = tomlkit.loads(toparse)
        self._parse_styles()

    def _parse_styles(self):
        """parse the styles section of the theme and put it into self.styles dict"""
        self.styles = {}
        try:
            for key, value in self.definition["styles"].items():
                self.styles[key] = rich.style.Style.parse(value)
        except KeyError:
            pass

    def has_domain(self, domain):
        """Check if the given domain exists."""
        try:
            _ = self.definition["domain"][domain]
            return True
        except KeyError:
            return False

    def domain_content(self, domain):
        "Extract all the data for a given domain, or an empty dict if there is none"
        content = {}
        try:
            content = self.definition["domain"][domain]
        except KeyError:
            # domain doesn't exist
            pass
        return content

    def domain_styles(self, domain):
        "Get all the styles for a given domain, or an empty dict of there are none"
        styles = {}
        try:
            raw_styles = self.definition["domain"][domain]["style"]
            # parse out the Style objects for each definition
            for key, value in raw_styles.items():
                styles[key] = self.get_style(value)
        except KeyError:
            pass
        return styles

    def domain_attributes(self, domain):
        "Get the non-style attributes of a domain"
        attributes = {}
        try:
            attributes = self.definition["domain"][domain].copy()
            # strip out the style subtable
            del attributes["style"]
        except KeyError:
            pass
        return attributes

    def get_style(self, styledef):
        """convert a string into rich.style.Style object"""
        try:
            style = self.styles[styledef]
        except KeyError:
            style = None
        if not style:
            style = rich.style.Style.parse(styledef)
        return style

    def render(self, domains=None):
        """render the output for a given domain, or all domains if none supplied

        domains can be a string with a single domain, a list of domains
        or None for all domains

        output is suitable for bash eval $()
        """
        renders = []
        if isinstance(domains, str):
            renders = [domains]
        elif domains:
            for one in domains:
                renders.append(one)
        else:
            for domain in self.definition["domain"].keys():
                renders.append(domain)

        for domain in renders:
            if self.has_domain(domain):
                content = self.domain_content(domain)
                attribs = self.domain_attributes(domain)
                # do the rendering that works in any domain
                self._environment_render(attribs, self.domain_styles(domain))
                # see if we have a processor defined for custom rendering
                try:
                    processor = attribs["processor"]
                except KeyError:
                    # no more to do for this domain, skip to the next iteration
                    # of the loop
                    continue
                try:
                    styles = self.domain_styles(domain)
                    if processor == "fzf":
                        self._fzf_render(domain, attribs, styles)
                    elif processor == "ls_colors":
                        self._ls_colors_render(domain, content)
                    elif processor == "iterm":
                        self._iterm_render(domain, content)
                    else:
                        # unknown processor specified in the domain, by
                        # definition, this is not an error, but you don't
                        # get any special rendering
                        pass
                except ThemeError as exc:
                    self.error_console.print(exc)
                    return self.EXIT_ERROR
            else:
                self.error_console.print(f"{self.prog}: {domain}: no such domain")
                return self.EXIT_ERROR
        return self.EXIT_SUCCESS

    def _environment_render(self, attribs, styles):
        """Render environment variables from a set of attributes and styles"""
        # render the variables to unset
        try:
            unsets = attribs["environment"]["unset"]
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
            exports = attribs["environment"]["export"]
            for var, value in exports.items():
                print(f'export {var}="{value}"')
        except KeyError:
            pass

    def _fzf_render(self, domain, attribs, styles):
        """render attribs into a shell statement to set an environment variable"""
        optstr = ""

        # process all the command line options
        try:
            opts = attribs["opt"]
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
        for name, style in styles.items():
            colors.append(self._fzf_from_style(name, style))
        # turn off all the colors, and add our color strings
        try:
            colorbase = f"{attribs['colorbase']},"
        except KeyError:
            colorbase = ""
        if colorbase or colors:
            colorstr = f" --color='{colorbase}{','.join(colors)}'"
        else:
            colorstr = ""

        # figure out which environment variable to put it in
        try:
            varname = attribs["environment_variable"]
            print(f'export {varname}="{optstr}{colorstr}"')
        except KeyError as exc:
            raise ThemeError(
                (
                    f"{self.prog}: fzf processor requires 'environment_variable'"
                    f" key to process domain '{domain}'"
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

    def _ls_colors_render(self, domain, content):
        "Render a LS_COLORS variable suitable for GNU ls"
        outlist = []
        # process the styles
        try:
            styles = content["style"]
        except KeyError:
            styles = {}
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = content["clear_builtin"]
            if not isinstance(clear_builtin, bool):
                errmsg = (
                    f"{self.prog}: ls_colors processor for"
                    f" domain '{domain}' requires 'clear_builtin' to be boolean"
                )
                raise ThemeError(errmsg)
        except KeyError:
            clear_builtin = False

        if clear_builtin:
            # iterate over all known styles
            for name in self.LS_COLORS_MAP:
                try:
                    styledef = styles[name]
                except KeyError:
                    # style isn't in our configuration, so put the default one in
                    styledef = "default"
                style = self.get_style(styledef)
                if style:
                    outlist.append(self._ls_colors_from_style(name, style))
        else:
            # iterate over the styles given in our configuration
            for name, styledef in styles.items():
                style = self.get_style(styledef)
                if style:
                    outlist.append(self._ls_colors_from_style(name, style))

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = content["environment_variable"]
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

    def _iterm_render(self, domain, content):
        """send the special escape sequences to make the iterm2
        terminal emulator for macos change its foreground and backgroud
        color

        echo "\033]1337;SetColors=bg=331111\007"
        """
        self._iterm_render_style(content, "foreground", "fg")
        self._iterm_render_style(content, "background", "bg")

    def _iterm_render_style(self, content, style, iterm_key):
        """print an iterm escape sequence to change the color palette"""
        try:
            styledef = content["style"][style]
            styleobj = self.get_style(styledef)
        except KeyError:
            pass
        if styleobj:
            clr = styleobj.color.get_truecolor()
            # gotta use raw strings here so the \033 and \007 don't get
            # interpreted by python
            out = r'builtin echo -n "\033]1337;'
            out += f"SetColors={iterm_key}={clr.hex.replace('#','')}"
            out += r'\007"'
            print(out)


class ThemeError(Exception):
    """Exception for theme processing errors"""
