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
"""class for storing and processing a pattern"""

import contextlib
import subprocess

import jinja2
import rich
import tomlkit

from .exceptions import DyeError, DyeSyntaxError
from .filters import jinja_filters
from .scope import Scope


class Pattern:
    """load and parse a pattern file into a pattern object"""

    @staticmethod
    def loads(tomlstring=None, theme=None):
        """Load a pattern from a given string, and return a new pattern object

        doesn't do any processing or applying of the pattern
        """
        if tomlstring:  # noqa: SIM108
            toparse = tomlstring
        else:
            # tomlkit can't parse None, so if we got it as the default
            # or if the caller pased None intentionally...
            toparse = ""
        pattern = Pattern()
        pattern.definition = tomlkit.loads(toparse)
        pattern._process(theme)
        return pattern

    @staticmethod
    def load(fobj, theme=None):
        """Load a pattern a file object

        doesn't do any processing or applying of the pattern
        """
        pattern = Pattern()
        pattern.definition = tomlkit.load(fobj)
        pattern._process(theme)

        return pattern

    #
    # initialization and properties
    #
    def __init__(self):
        """Construct a new Pattern object"""

        # the raw toml definition of the pattern
        self.definition = {}

        # these contain the core parts of the pattern,
        # but they have all been processed through the template
        # so they can be used by consumers of our class.
        # these are all set by process()
        self.colors = {}
        self.styles = {}
        self.variables = {}
        self.scopes = {}

    @property
    def description(self):
        """get the description from self.definition

        returns None if the element is not present in the toml
        """
        try:
            return self.definition["description"]
        except KeyError:
            return None

    @property
    def prevent_themes(self):
        """returns true if this pattern won't let you apply external themes"""
        out = False
        with contextlib.suppress(KeyError):
            out = self.definition["prevent_themes"]
            if not isinstance(out, bool):
                raise DyeSyntaxError("'prevent_themes' must be true or false")
        return out

    @property
    def requires_theme(self):
        """get the requires_theme setting from the definition

        returns None if the element is not present in the toml
        """
        try:
            return self.definition["requires_theme"]
        except KeyError:
            return None

    def _process(self, theme=None):
        """Process the loaded pattern definition, merging in a theme if given

        returns nothing, populates stuff in the current object:

            .colors
            .styles
            .variables
            .scopes
        """
        jinja_env = jinja2.Environment()
        jinja_env.filters = jinja_filters()

        self._process_colors(jinja_env, theme)
        self._process_styles(jinja_env, theme)
        self._process_variables(jinja_env)
        self._process_scopes()

    def _process_colors(self, jinja_env, theme=None):
        """merge the colors from this pattern and the given theme together

        this sets self.colors

        A color can be referenced in this section in any of three ways:

        foreground = "#f8f8f2"
        foreground_high = "foreground"
        foreground_medium = "{{ colors.foreground }}"
        foreground_low = "{{ color.foreground }}"

        A color is just a string, there is nothing done to the value of the color.
        You could do everything with a variable that you can do with a color,
        it's just a convenient way to group/name them.
        """
        merged_colors = theme.colors.copy() if theme else {}

        pattern_colors = {}
        with contextlib.suppress(KeyError):
            pattern_colors = self.definition["colors"]

        # go through the pattern colors one at a time, rendering them,
        #     and adding them to merged_colors
        # one intentional side effect is that if you define a color in
        #     your pattern that has already been defined in the theme,
        #     the definition in the pattern will over-ride
        # we also pass the growing list of merged_colors as context

        # do a bare lookup so that foreground_low = "foreground" works
        for key, value in pattern_colors.items():
            if value in merged_colors:
                merged_colors[key] = merged_colors[value]
            else:
                template = jinja_env.from_string(value)
                # this lets us do {{colors.foreground}} or {{color.foreground}}
                merged_colors[key] = template.render(
                    color=merged_colors, colors=merged_colors
                )

        self.colors = merged_colors

    def _process_styles(self, jinja_env, theme=None):
        """merge the styles from this pattern and the given theme together

        this sets self.styles
        """
        merged_styles = theme.styles.copy() if theme else {}

        pattern_styles = {}
        with contextlib.suppress(KeyError):
            pattern_styles = self.definition["styles"]

        # go through the pattern styles one at a time, rendering them,
        #     and adding them to merged_colors
        # one intentional side effect is that if you define a style in
        #     your pattern that has already been defined in the theme,
        #     the definition in the pattern will over-ride
        # we also pass the colors and the growing list of merged_styles
        #     as context
        for key, value in pattern_styles.items():
            # do a bare lookup so that text_low = "text" works
            if value in merged_styles:
                merged_styles[key] = merged_styles[value]
            else:
                template = jinja_env.from_string(value)
                # allow {{style.foreground}} or {{styles.foreground}}
                # or {{color.background}} or {{colors.background}}
                rendered = template.render(
                    color=self.colors,
                    colors=self.colors,
                    style=merged_styles,
                    styles=merged_styles,
                )
                merged_styles[key] = rich.style.Style.parse(rendered)

        self.styles = merged_styles

    def _process_variables(self, jinja_env):
        """process the variables into self.variables"""
        # Process the capture variables without rendering.
        # We can't render because the toml parser has to group
        # all the "capture" items in a separate table, they can't be
        # interleaved with the regular variables in the order they are
        # defined. So we have to choose to process either the [variables]
        # table or the [variables][capture] table first. We choose the
        # [variables][capture] table.
        #
        # no technical reason why we don't render colors and styles
        # in capture variables
        processed_vars = {}
        try:
            cap_vars = self.definition["variables"]["capture"]
        except KeyError:
            cap_vars = {}
        for var, cmd in cap_vars.items():
            proc = subprocess.run(cmd, shell=True, check=False, capture_output=True)
            if proc.returncode != 0:
                raise DyeError(
                    f"capture variable '{var}' returned a non-zero exit code."
                )
            processed_vars[var] = str(proc.stdout, "UTF-8")

        # then add the regular variables, processing them as templates
        try:
            # make a shallow copy, because we are gonna delete any capture
            # vars and we want the definition to stay pristine
            reg_vars = self.definition["variables"].copy()
        except KeyError:
            reg_vars = {}
        # if no capture variables, we don't care, if present
        # delete that table so we don't process it again
        with contextlib.suppress(KeyError):
            del reg_vars["capture"]

        for var, definition in reg_vars.items():
            if var in processed_vars:
                raise DyeError(f"variable '{var}' has already been defined.")
            template = jinja_env.from_string(definition)
            processed_vars[var] = template.render(
                color=self.colors,
                colors=self.colors,
                style=self.styles,
                styles=self.styles,
                var=processed_vars,
                vars=processed_vars,
                variable=processed_vars,
                variables=processed_vars,
            )

        self.variables = processed_vars

    def _process_scopes(self):
        """process value in every scope as a template to resolve
        colors, styles, and variables

        sets self.scopes as a dict of objects
        """
        raw_scopes = {}
        with contextlib.suppress(KeyError):
            raw_scopes = self.definition["scopes"]

        for name in raw_scopes:
            scope = Scope.extract(self, name)
            self.scopes[name] = scope

    #
    # scope methods
    #
    def has_scope(self, scope):
        """Check if the given scope exists."""
        return scope in self.scopes
