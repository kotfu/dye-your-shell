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
"""agent implementations and their base class"""

import abc
import contextlib
import re

import rich.color

from .exceptions import DyeError, DyeSyntaxError


class AgentBase(abc.ABC):
    """Abstract Base Class for all agents

    Subclass and implement `run()`. The first line of the class docstring
    is displayed by `shell-themer agents` as the description of the agent

    Creates a registry of all subclasses in cls.agents

    The string to use in your theme configuration file is the underscored
    class name, ie:

    EnvironmentVariables -> environment_variables
    GnuLs -> gnu_ls
    """

    classmap = {}

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        # make a registry of subclasses as they are defined
        cls.classmap[cls._name_of(cls.__name__)] = cls

    def __init__(self, scope, pattern):
        super().__init__()
        self.agent = self._name_of(self.__class__.__name__)
        self.scope = scope
        self.scopedef = pattern.scopes[scope]
        self.pattern = pattern
        self.scope_styles = self._process_scope_styles()

    def _process_scope_styles(self):
        # create scope_styles, the styles parsed from scopedef
        try:
            raw_styles = self.scopedef["styles"]
        except (KeyError, TypeError):
            raw_styles = {}

        processed_styles = {}
        for name, styledef in raw_styles.items():
            processed_styles[name] = rich.style.Style.parse(styledef)

        return processed_styles

    @classmethod
    def _name_of(cls, name: str) -> str:
        """Make an underscored, lowercase form of the given class name."""
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        name = name.replace("-", "_")
        return name.lower()

    @abc.abstractmethod
    def run(self) -> str:
        """Do agent work. Anything returned will be sourced by the shell"""


class LsColorsFromStyle:
    """Generator mixin to create ls_colors type styles"""

    def ls_colors_from_style(self, name, style, mapp, scope, allow_unknown=False):
        """create an entry suitable for LS_COLORS from a style

        name should be a valid LS_COLORS entry, could be a code representing
        a file type, or a glob representing a file extension

        style is a style object

        mapp is a dictionary of friendly color names to native color names
            ie map['directory'] = 'di'

        allow_unknown - whether to allow [name] that is not in [mapp]. If false,
        an error will be generated if you use a [name] that is not in [mapp]. If
        true, [mapp] will only be used as a "friendly" name lookup.

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
            if allow_unknown:
                # no problem if we didn't find name in mapp, we'll just use name
                # as is
                mapname = name
            else:
                # they used a style for a file attribute that isn't in the map
                # which is not allowed
                raise DyeError(
                    f"unknown style '{name}' while processing" f" scope '{scope}'"
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


class EnvironmentVariables(AgentBase):
    "Export and unset environment variables"

    def run(self) -> str:
        output = []
        try:
            unsets = self.scopedef["unset"]
            if isinstance(unsets, str):
                # if they used a string in the config file instead of a list
                # process it like a single item instead of trying to process
                # each letter in the string
                unsets = [unsets]
            for var in unsets:
                output.append(f"unset {var}")
        except KeyError:
            # no unsets
            pass
        # render the variables to export
        try:
            exports = self.scopedef["export"]
            for var, value in exports.items():
                output.append(f'export {var}="{value}"')
        except KeyError:
            # no exports
            pass
        return "\n".join(output)


class Eza(AgentBase, LsColorsFromStyle):
    "Create EZA_COLORS environment variable for use with ls replacement eza"

    EZA_COLORS_BASE_MAP = {
        # create a map of friendly names to real codes.
        # we use the same friendly names as the theme.yml
        # file used by eza
        #
        "filekinds:normal": "fi",
        "filekinds:directory": "di",
        "filekinds:symlink": "ln",
        "filekinds:pipe": "pi",
        "filekinds:block_device": "bd",
        "filekinds:char_device": "cd",
        "filekinds:socket": "so",
        "filekinds:special": "sp",
        "filekinds:executable": "ex",
        "filekinds:mount_point": "mp",
        #
        "perms:user_read": "ur",
        "perms:user_write": "uw",
        "perms:user_executable_file": "ux",
        "perms:user_execute_other": "ue",
        "perms:group_read": "gr",
        "perms:group_write": "gw",
        "perms:group_execute": "gx",
        "perms:other_read": "tr",
        "perms:other_write": "tw",
        "perms:other_execute": "tx",
        "perms:special_user_file": "su",
        "perms:special_other": "sf",
        "perms:attribute": "xa",
        #
        "size:major": "df",
        "size:minor": "ds",
        "size:number_style": "sn",
        "size:number_byte": "nb",
        "size:number_kilo": "nk",
        "size:number_mega": "nm",
        "size:number_giga": "ng",
        "size:number_huge": "nt",
        "size:unit_style": "sb",
        "size:unit_byte": "ub",
        "size:unit_kilo": "uk",
        "size:unit_mega": "um",
        "size:unit_giga": "ug",
        "size:unit_huge": "ut",
        #
        "users:user_you": "uu",
        "users:user_other": "un",
        "users:user_root": "uR",
        "users:group_yours": "gu",
        "users:group_other": "gn",
        "users:group_root": "gR",
        #
        "links:normal": "lc",
        "links:multi_link_file": "lm",
        #
        "git:new": "ga",
        "git:modified": "gm",
        "git:deleted": "gd",
        "git:renamed": "gv",
        "git:typechange": "gt",
        "git:ignored": "gi",
        "git:conflicted": "gc",
        #
        "git_repo:branch_main": "Gm",
        "git_repo:branch_other": "Go",
        "git_repo:git_clean": "Gc",
        "git_repo:git_dirty": "Gd",
        #
        "selinux:colon": "Sn",
        "selinux:user": "Su",
        "selinux:role": "Sr",
        "selinux:typ": "St",
        "selinux:range": "Sl",
        #
        "file_type:image": "im",
        "file_type:video": "vi",
        "file_type:music": "mu",
        "file_type:lossless": "lo",
        "file_type:crypto": "cr",
        "file_type:document": "do",
        "file_type:compressed": "co",
        "file_type:temp": "tm",
        "file_type:compiled": "cm",
        "file_type:build": "bu",
        "file_type:source": "sc",
        #
        "punctuation": "xx",
        "date": "da",
        "inode": "in",
        "blocks": "bl",
        "header": "hd",
        "octal": "oc",
        "flags": "ff",
        "symlink_path": "lp",
        "control_char": "cc",
        "broken_path_overlay": "b0",
        "broken_symlink": "or",
    }
    # this map allows you to either use the 'native' eza code, or the
    # 'friendly' name defined by shell-themer
    EZA_COLORS_MAP = {}
    for friendly, actual in EZA_COLORS_BASE_MAP.items():
        EZA_COLORS_MAP[friendly] = actual
        EZA_COLORS_MAP[actual] = actual

    def run(self):
        "Render a EZA_COLORS variable suitable for eza"
        outlist = []
        # figure out if we are clearing builtin styles
        with contextlib.suppress(KeyError):
            clear_builtin = self.scopedef["clear_builtin"]
            if not isinstance(clear_builtin, bool):
                raise DyeSyntaxError(
                    f"scope '{self.scope}' requires 'clear_builtin' to be true or false"
                )
            if clear_builtin:
                # this tells exa to not use any built-in/hardcoded colors
                outlist.append("reset")

        # iterate over the styles given in our configuration
        for name, style in self.scope_styles.items():
            if style:
                _, render = self.ls_colors_from_style(
                    name,
                    style,
                    self.EZA_COLORS_MAP,
                    allow_unknown=True,
                    scope=self.scope,
                )
                outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = self.scopedef["environment_variable"]
        except KeyError:
            varname = "EZA_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        print(f'''export {varname}="{':'.join(outlist)}"''')


class Fzf(AgentBase):
    "Set fzf options and environment variables"

    def run(self) -> str:
        """render attribs into a shell statement to set an environment variable"""
        optstr = ""
        # process all the command line options
        try:
            opts = self.scopedef["opts"]
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
        except KeyError:
            varname = "FZF_DEFAULT_OPTS"
        print(f'export {varname}="{optstr}{colorstr}"')

    def _fzf_from_style(self, name, style):
        """turn a rich.style into a valid fzf color"""
        # fzf has different color names for foreground and background items
        # we combine them
        name_map = {
            "text": ("fg", "bg"),
            "current-line": ("fg+", "bg+"),
            "selected-line": ("selected-fg", "selected-bg"),
            "preview": ("preview-fg", "preview-bg"),
        }

        fzf_colors = []
        if name in name_map:
            fgname, bgname = name_map[name]
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf_colors.append(f"{fgname}:{fzfc}:{fzfa}")
            if style.bgcolor:
                fzfc = self._fzf_color_from_rich_color(style.bgcolor)
                fzf_colors.append(f"{bgname}:{fzfc}")
        else:
            # we only use the foreground color of the style, and ignore
            # any background color specified by the style
            if style.color:
                fzfc = self._fzf_color_from_rich_color(style.color)
                fzfa = self._fzf_attribs_from_style(style)
                fzf_colors.append(f"{name}:{fzfc}:{fzfa}")

        return ",".join(fzf_colors)

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


class GnuLs(AgentBase, LsColorsFromStyle):
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

    def run(self):
        "Render a LS_COLORS variable suitable for GNU ls"
        outlist = []
        havecodes = []
        # figure out if we are clearing builtin styles
        try:
            clear_builtin = self.scopedef["clear_builtin"]
            if not isinstance(clear_builtin, bool):
                raise DyeSyntaxError(
                    f"scope '{self.scope}' requires 'clear_builtin' to be true or false"
                )
        except KeyError:
            clear_builtin = False

        # iterate over the styles given in our configuration
        for name, style in self.scope_styles.items():
            if style:
                mapcode, render = self.ls_colors_from_style(
                    name,
                    style,
                    self.LS_COLORS_MAP,
                    self.scope,
                    allow_unknown=False,
                )
                havecodes.append(mapcode)
                outlist.append(render)

        if clear_builtin:
            style = rich.style.Style.parse("default")
            # go through all the color codes, and render them with the
            # 'default' style and add them to the output
            for name, code in self.LS_COLORS_BASE_MAP.items():
                if code not in havecodes:
                    _, render = self.ls_colors_from_style(
                        name,
                        style,
                        self.LS_COLORS_MAP,
                        allow_unknown=False,
                        scope=self.scope,
                    )
                    outlist.append(render)

        # process the filesets

        # figure out which environment variable to put it in
        try:
            varname = self.scopedef["environment_variable"]
        except KeyError:
            varname = "LS_COLORS"

        # even if outlist is empty, we have to set the variable, because
        # when we are switching a theme, there may be contents in the
        # environment variable already, and we need to tromp over them
        # we chose to set the variable to empty instead of unsetting it
        return f'''export {varname}="{':'.join(outlist)}"'''


class Iterm(AgentBase):
    "Send escape sequences to iTerm terminal emulator"

    def run(self):
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
        with contextlib.suppress(KeyError):
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
                # in iterm you have to send different escape sequences
                #
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
        """create echo commands to change the cursor shape,
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
                raise DyeSyntaxError(
                    f"unknown cursor '{cursor}'"
                    f" while processing scope '{self.scope}'"
                )
        # render the cursor color
        # iterm has curbg and curfg color codes, but as far as I can tell
        # the curfg is a noop
        self._iterm_render_style(output, "cursor", "curbg")

    def _iterm_render_style(self, output, style_name, iterm_key):
        """append an iterm escape sequence to change the color palette to output"""
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


class Shell(AgentBase):
    "Execute arbitary shell commands"

    def run(self):
        output = []
        try:
            cmds = self.scopedef["command"]
            for _, cmd in cmds.items():
                output.append(cmd)
        except KeyError:
            pass
        return "\n".join(output)
