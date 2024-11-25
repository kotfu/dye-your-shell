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
"""generator implementations and their base class"""

import abc
import re

import rich.color

from .exceptions import ThemeError
from .interpolator import Interpolator
from .parsers import StyleParser
from .utils import AssertBool


class GeneratorBase(abc.ABC, AssertBool):
    """Abstract Base Class for all generators

    Subclass and implement `generate()`. The first line of the class docstring
    is displayed by `shell-themer generators` as the description of the generator

    Creates a registry of all subclasses in cls.generators

    The string to use in your theme configuration file is the underscored
    class name, ie:

    EnvironmentVariables -> environment_variables
    LsColors -> ls_colors
    """

    classmap = {}

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        # make a registry of subclasses as they are defined
        cls.classmap[cls._name_of(cls.__name__)] = cls

    def __init__(self, scopedef, styles, variables, prog=None, scope=None):
        super().__init__()
        self.generator = self._name_of(self.__class__.__name__)
        self.scopedef = scopedef
        self.styles = styles
        self.variables = variables
        self.prog = prog
        self.scope = scope
        # create scope_styles, the styles parsed from scopedef
        try:
            raw_styles = scopedef["style"]
        except (KeyError, TypeError):
            raw_styles = {}
        parser = StyleParser(styles, variables)
        self.scope_styles = parser.parse_dict(raw_styles)
        # create an interpolator
        self.interp = Interpolator(
            self.styles, self.variables, prog=self.prog, scope=self.scope
        )

    @classmethod
    def _name_of(cls, name: str) -> str:
        """Make an underscored, lowercase form of the given class name."""
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        name = name.replace("-", "_")
        return name.lower()

    @abc.abstractmethod
    def generate(self) -> str:
        """generate a string of text, with newlines, which can be sourced by bash"""


class LsColorsFromStyle:
    """Generator mixin to create ls_colors type styles"""

    def ls_colors_from_style(self, name, style, mapp, **msgdata):
        """create an entry suitable for LS_COLORS from a style

        name should be a valid LS_COLORS entry, could be a code representing
        a file type, or a glob representing a file extension

        style is a style object

        mapp is a dictionary of friendly color names to native color names
            ie map['directory'] = 'di'

        **msgdata - used for generating useful error messages
        prog = the name of the program
        scope = is the scope where this mapped occured

        returns a tuple of the mapped name and a phrase to add to LS_COLORS
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
                f"{msgdata['prog']}: unknown style '{name}' while processing"
                f" scope '{msgdata['scope']}'"
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


class EnvironmentVariables(GeneratorBase):
    "Export and unset environment variables"

    def generate(self) -> str:
        output = []
        try:
            unsets = self.scopedef["unset"]
            if isinstance(unsets, str):
                # if they used a string in the config file instead of a list
                # process it like a single item instead of trying to process
                # each letter in the string
                unsets = [unsets]
            for unset in unsets:
                output.append(f"unset {self.interp.interpolate(unset)}")
        except KeyError:
            # no unsets
            pass
        # render the variables to export
        try:
            exports = self.scopedef["export"]
            for var, value in exports.items():
                new_var = self.interp.interpolate(var)
                new_value = self.interp.interpolate(value)
                output.append(f'export {new_var}="{new_value}"')
        except KeyError:
            # no exports
            pass
        return "\n".join(output)


class Fzf(GeneratorBase):
    "Set fzf options and environment variables"

    def generate(self) -> str:
        """render attribs into a shell statement to set an environment variable"""
        optstr = ""
        # process all the command line options
        try:
            opts = self.scopedef["opt"]
        except KeyError:
            opts = {}

        for key, value in opts.items():
            if isinstance(value, str):
                interp_value = self.interp.interpolate(value)
                optstr += f" {key}='{interp_value}'"
            elif isinstance(value, bool) and value:
                optstr += f" {key}"

        # process all the styles
        colors = []
        # then add them back
        for name, style in self.scope_styles.items():
            colors.append(self._fzf_from_style(name, style))
        # turn off all the colors, and add our color strings
        try:
            colorbase = f"{self.scopedef['colorbase']},"
        except KeyError:
            colorbase = ""
        if colorbase or colors:
            colorstr = f" --color='{colorbase}{','.join(colors)}'"
        else:
            colorstr = ""

        # figure out which environment variable to put it in
        try:
            varname = self.scopedef["environment_variable"]
            varname = self.interp.interpolate(varname)
            print(f'export {varname}="{optstr}{colorstr}"')
        except KeyError as exc:
            raise ThemeError(
                f"{self.prog}: fzf generator requires 'environment_variable'"
                f" key to process scope '{self.scope}'"
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


class LsColors(GeneratorBase, LsColorsFromStyle):
    "Create LS_COLORS environment variable for use with GNU ls"

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

    def generate(self):
        "Render a LS_COLORS variable suitable for GNU ls"
        outlist = []
        havecodes = []
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = self.scopedef["clear_builtin"]
            self.assert_bool(
                clear_builtin,
                key="clear_builtin",
                generator=self.generator,
                prog=self.prog,
                scope=self.scope,
            )
        except KeyError:
            clear_builtin = False

        # iterate over the styles given in our configuration
        for name, style in self.scope_styles.items():
            if style:
                mapcode, render = self.ls_colors_from_style(
                    name, style, self.LS_COLORS_MAP, prog=self.prog, scope=self.scope
                )
                havecodes.append(mapcode)
                outlist.append(render)

        if clear_builtin:
            style_parser = StyleParser(None, None)
            style = style_parser.parse_text("default")
            # go through all the color codes, and render them with the
            # 'default' style and add them to the output
            for name, code in self.LS_COLORS_BASE_MAP.items():
                if code not in havecodes:
                    _, render = self.ls_colors_from_style(
                        name,
                        style,
                        self.LS_COLORS_MAP,
                        prog=self.prog,
                        scope=self.scope,
                    )
                    outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = self.scopedef["environment_variable"]
            varname = self.interp.interpolate(varname)
        except KeyError:
            varname = "LS_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        return f'''export {varname}="{':'.join(outlist)}"'''


class ExaColors(GeneratorBase, LsColorsFromStyle):
    "Create EXA_COLORS environment variable for use with ls replacement exa"

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

    def generate(self):
        "Render a EXA_COLORS variable suitable for exa"
        outlist = []
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = self.scopedef["clear_builtin"]
            self.assert_bool(
                clear_builtin,
                key="clear_builtin",
                generator=self.generator,
                prog=self.prog,
                scope=self.scope,
            )
        except KeyError:
            clear_builtin = False

        if clear_builtin:
            # this tells exa to not use any built-in/hardcoded colors
            outlist.append("reset")

        # iterate over the styles given in our configuration
        for name, style in self.scope_styles.items():
            if style:
                _, render = self.ls_colors_from_style(
                    name, style, self.EXA_COLORS_MAP, prog=self.prog, scope=self.scope
                )
                outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = self.scopedef["environment_variable"]
            varname = self.interp.interpolate(varname)
        except KeyError:
            varname = "EXA_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        print(f'''export {varname}="{':'.join(outlist)}"''')


class EzaColors(GeneratorBase, LsColorsFromStyle):
    "Create EZA_COLORS environment variable for use with ls replacement eza"

    #
    # this is basically the same as the exa generator, but it's
    # copied instead of refactored becasue exa will probably go
    # away soon
    #
    # eza color generator
    #
    EZA_COLORS_BASE_MAP = {
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
    EZA_COLORS_MAP = {}
    for friendly, actual in EZA_COLORS_BASE_MAP.items():
        EZA_COLORS_MAP[friendly] = actual
        EZA_COLORS_MAP[actual] = actual

    def generate(self):
        "Render a EZA_COLORS variable suitable for eza"
        outlist = []
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = self.scopedef["clear_builtin"]
            self.assert_bool(
                clear_builtin,
                key="clear_builtin",
                generator=self.generator,
                prog=self.prog,
                scope=self.scope,
            )
        except KeyError:
            clear_builtin = False

        if clear_builtin:
            # this tells exa to not use any built-in/hardcoded colors
            outlist.append("reset")

        # iterate over the styles given in our configuration
        for name, style in self.scope_styles.items():
            if style:
                _, render = self.ls_colors_from_style(
                    name, style, self.EZA_COLORS_MAP, prog=self.prog, scope=self.scope
                )
                outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = self.scopedef["environment_variable"]
            varname = self.interp.interpolate(varname)
        except KeyError:
            varname = "EZA_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        print(f'''export {varname}="{':'.join(outlist)}"''')


class Iterm(GeneratorBase):
    "Send escape sequences to iTerm terminal emulator"

    def generate(self):
        """send escape sequences to iTerm to make it do stuff"""
        output = []

        # set the profile
        self._iterm_profile(output)

        # set the tab or window title color
        self._iterm_tab(output)

        # set foreground and background colors
        self._iterm_render_style(output, "foreground", "fg")
        self._iterm_render_style(output, "background", "bg")

        # set the cursor shape and color
        self._iterm_cursor(output)

        return "\n".join(output)

    def _iterm_profile(self, output):
        """add commands to output to tell iterm to change to a profile"""
        try:
            profile = self.scopedef["profile"]
            cmd = r'builtin echo -en "\e]1337;'
            cmd += f"SetProfile={profile}"
            cmd += r'\a"'
            output.append(cmd)
        except KeyError:
            # no profile directive given
            pass

    def _iterm_tab(self, output):
        """add commands to output to change the tab or window title background color"""
        try:
            style = self.scope_styles["tab"]
            if style.color.is_default:
                # set the command to change the tab color back to the default,
                # meaning whatever is set in the profile.
                # gotta use raw strings here so the \e and \a don't get
                # interpreted by python, they need to be passed through
                # to the echo command
                cmd = r'builtin echo -en "\e]6;1;bg;*;default\a"'
                output.append(cmd)
            else:
                clr = style.color.get_truecolor()
                # gotta use raw strings here so the \e and \a don't get
                # interpreted by python, they need to be passed through
                # to the echo command
                cmd = r'builtin echo -en "\e]6;1;bg;red;brightness;'
                cmd += f"{clr.red}"
                cmd += r'\a"'
                output.append(cmd)
                cmd = r'builtin echo -en "\e]6;1;bg;green;brightness;'
                cmd += f"{clr.green}"
                cmd += r'\a"'
                output.append(cmd)
                cmd = r'builtin echo -en "\e]6;1;bg;blue;brightness;'
                cmd += f"{clr.blue}"
                cmd += r'\a"'
                output.append(cmd)
        except KeyError:
            pass

    CURSOR_MAP = {
        "block": "0",
        "box": "0",
        "vertical_bar": "1",
        "vertical": "1",
        "bar": "1",
        "pipe": "1",
        "underline": "2",
    }

    def _iterm_cursor(self, output):
        """generate echo commands to change the cursor shape,
        foreground, and background colors
        """
        # check the cursor shape
        try:
            cursor = self.scopedef["cursor"]
        except KeyError:
            cursor = None
        if cursor:
            if cursor == "profile":
                cmd = r'builtin echo -en "\e[0q"'
                output.append(cmd)
            elif cursor in self.CURSOR_MAP:
                cmd = r'builtin echo -en "\e]1337;'
                cmd += f"CursorShape={self.CURSOR_MAP[cursor]}"
                cmd += r'\a"'
                output.append(cmd)
            else:
                raise ThemeError(
                    f"{self.prog}: unknown cursor '{cursor}'"
                    f" while processing scope '{self.scope}'"
                )
        # render the cursor color
        # iterm has curbg and curfg color codes, but as far as I can tell
        # the curfg is a noop
        self._iterm_render_style(output, "cursor", "curbg")

    def _iterm_render_style(self, output, style_name, iterm_key):
        """print an iterm escape sequence to change the color palette"""
        try:
            style = self.scope_styles[style_name]
            clr = style.color.get_truecolor()
            # gotta use raw strings here so the \e and \a don't get
            # interpreted by python, they need to be passed through
            # to the echo command
            cmd = r'builtin echo -en "\e]1337;'
            cmd += f"SetColors={iterm_key}={clr.hex.replace('#','')}"
            cmd += r'\a"'
            output.append(cmd)
        except KeyError:
            # the given style doesn't exist
            pass


class Shell(GeneratorBase):
    "Execute arbitary shell commands"

    def generate(self):
        out = []
        try:
            cmds = self.scopedef["command"]
            for _, cmd in cmds.items():
                out.append(self.interp.interpolate(cmd))
        except KeyError:
            pass
        return "\n".join(out)
