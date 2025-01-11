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
"""classes for storing a pattern"""

import contextlib
import subprocess

import jinja2
import rich
import tomlkit

from .exceptions import DyeError, DyeSyntaxError
from .filters import jinja_filters


class Pattern:
    """load and parse a pattern file into a theme object"""

    @classmethod
    def loads(cls, tomlstring=None):
        """Load a pattern from a given string, and return a new pattern object

        doesn't do any processing or applying of the pattern
        """
        if tomlstring:  # noqa: SIM108
            toparse = tomlstring
        else:
            # tomlkit can't parse None, so if we got it as the default
            # or if the caller pased None intentionally...
            toparse = ""
        pattern = cls()
        pattern.definition = tomlkit.loads(toparse)
        return pattern

    @classmethod
    def load(cls, fobj):
        """Load a pattern a file object

        doesn't do any processing or applying of the pattern
        """
        pattern = cls()
        pattern.definition = tomlkit.load(fobj)
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

    def process(self, theme=None):
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
        self._process_scopes(jinja_env)

    def _process_colors(self, jinja_env, theme=None):
        """merge the colors from this pattern and the given theme together

        this sets self.colors
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
        for key, value in pattern_colors.items():
            template = jinja_env.from_string(value)
            merged_colors[key] = template.render(colors=merged_colors)

        self.colors = merged_colors

    def _process_styles(self, jinja_env, theme=None):
        """merge the styles from this pattern and the given theme together

        this sets self.styles
        """
        merged_styles = theme.colors.copy() if theme else {}

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
            template = jinja_env.from_string(value)
            rendered = template.render(colors=self.colors, styles=merged_styles)
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

        # then add the regular variables, interpolating as we go
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
                colors=self.colors, styles=self.styles, variables=processed_vars
            )

        self.variables = processed_vars

    def _process_scopes(self, jinja_env):
        """process value in every scope as a template to resolve
        colors, styles, and variables

        sets self.scopes
        """

        def render_func(value):
            template = jinja_env.from_string(value)
            return template.render(
                colors=self.colors,
                styles=self.styles,
                variables=self.variables,
            )

        try:
            scopes = self.definition["scopes"]
            self.scopes = self._process_nested_dict(scopes, render_func)
        except KeyError:
            # no [scopes] present
            self.scopes = {}

    def _process_nested_dict(self, dataset, render_func):
        """recursive function to crawl through a dictionary and
        call render_func for every nested dict and list item

        """
        result = {}
        for key, value in dataset.items():
            if isinstance(value, dict):
                result[key] = self._process_nested_dict(value, render_func)
            elif isinstance(value, list):
                result[key] = map(render_func, value)
            elif isinstance(value, str):
                result[key] = render_func(value)
            else:
                # don't try and render non-string values
                result[key] = value
        return result

    #
    # scope methods
    #
    def has_scope(self, scope):
        """Check if the given scope exists."""
        return scope in self.definition["scopes"]

    def is_scope_enabled(self, scope):
        """Determine if the scope is enabled
        The default is that the scope is enabled

        If can be disabled by:

            enabled = false

        or:
            enabled_if = "{shell cmd}" returns a non-zero exit code

        if 'enabled = false' is present, then enabled_if is not checked

        Throws KeyError if scope does not exist
        """
        scopedef = self.scopes[scope]
        with contextlib.suppress(KeyError):
            enabled = scopedef["enabled"]
            if not isinstance(enabled, bool):
                raise DyeSyntaxError(
                    f"scope '{scope}' requires 'enabled' to be true or false"
                )
            # this is authoritative, if it exists, ignore enabled_if below
            return enabled

        # no enabled directive, so we check for enabled_if
        try:
            enabled_if = scopedef["enabled_if"]
            if not enabled_if:
                # we have a key, but an empty value (aka command)
                # by rule we say it's enabled
                return True
        except KeyError:
            # no enabled_if key, so we must be enabled
            return True

        # if we get here we have something in enabled_if that
        # we need to go run
        env = jinja2.Environment()
        template = env.from_string(enabled_if)
        resolved_cmd = template.render(
            colors=self.colors, styles=self.styles, variables=self.variables
        )

        proc = subprocess.run(
            resolved_cmd, shell=True, check=False, capture_output=True
        )
        if proc.returncode != 0:  # noqa: SIM103
            # the shell command returned a non-zero exit code
            # and this scope should therefore be disabled
            return False
        return True
