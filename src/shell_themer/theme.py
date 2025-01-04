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
"""classes for storing a theme"""

import contextlib
import subprocess

import tomlkit

from .exceptions import ThemeError
from .interpolator import Interpolator
from .parsers import StyleParser
from .utils import AssertBool


class Theme(AssertBool):
    """load and parse a theme file into a theme object"""

    #
    # initialization and properties
    #
    def __init__(self, prog):
        """Construct a new Theme object"""
        self.prog = prog

        self.definition = {}
        self.styles = {}
        self.variables = {}

        # a place to stash the file that the theme was loaded from
        # it's up to the caller/user to make sure this is set properly
        # defaults to None
        self.theme_file = None

        self.loads()

    def loads(self, tomlstring=None):
        """Load a theme from a given string"""
        if tomlstring:  # noqa: SIM108
            toparse = tomlstring
        else:
            # tomlkit can't parse None, so if we got it as the default
            # or if the caller pased None intentionally...
            toparse = ""
        self.definition = tomlkit.loads(toparse)
        self._process_definition()

    def load(self, fobj):
        """Load a theme from a file object"""
        self.definition = tomlkit.load(fobj)
        # self.theme_file = fname
        self._process_definition()

    def _process_definition(self):
        """process a newly loaded definition, including variables and styles

        this sets self.styles and self.variables
        """
        # process the styles, with no base styles or variables
        parser = StyleParser(None, None)
        try:
            raw_styles = self.definition["styles"]
        except KeyError:
            raw_styles = {}
        self.styles = parser.parse_dict(raw_styles)
        # Process the capture variables, without interpolation.
        # We can't interpolate because the toml parser has to group
        # all the "capture" items in a separate table, they can't be
        # interleaved with the regular variables in the order they are
        # defined. So we have to choose to process either the [variables]
        # table or the [variables][capture] table first. We choose the
        # [variables][capture] table.
        resolved_vars = {}
        try:
            cap_vars = self.definition["variables"]["capture"]
        except KeyError:
            cap_vars = {}
        for var, cmd in cap_vars.items():
            proc = subprocess.run(cmd, shell=True, check=False, capture_output=True)
            if proc.returncode != 0:
                raise ThemeError(
                    f"{self.prog}: capture variable '{var}' returned"
                    " a non-zero exit code."
                )
            resolved_vars[var] = str(proc.stdout, "UTF-8")
        # then add the regular variables, interpolating as we go
        try:
            # make a shallow copy, because we are gonna delete something
            # and we want the definition to stay pristine
            reg_vars = dict(self.definition["variables"])
        except KeyError:
            reg_vars = {}
        # if no capture variables, we don't care
        with contextlib.suppress(KeyError):
            del reg_vars["capture"]

        for var, defined in reg_vars.items():
            if var in resolved_vars:
                raise ThemeError(
                    f"{self.prog}: a variable named '{var}' is already defined."
                )
            # create a new interpolator each time through the loop so
            # we can interpolate variables into other variables as they
            # are defined
            interp = Interpolator(
                self.styles, resolved_vars, prog=self.prog, scope="variables"
            )
            resolved_vars[var] = interp.interpolate(defined)

        # finally set the variables on this object, which will be used by a
        # lot of other stuff
        self.variables = resolved_vars

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
        # key error if scope doesn't exist, which is fine
        with contextlib.suppress(KeyError):
            scopedef = self.definition["scope"][scope]
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
            self.assert_bool(
                enabled,
                key="enabled",
                prog=self.prog,
                scope=scope,
            )
            # this is authoritative, if it exists, ignore enabled_if below
            return enabled
        except KeyError:
            # no enabled command, but we need to still keep checking
            pass

        try:
            enabled_if = scopedef["enabled_if"]
            if not enabled_if:
                # we have a key, but an empty value (aka command)
                # by rule we say it's enabled
                return True
        except KeyError:
            # no enabled_if key, so we must be enabled
            return True

        interp = Interpolator(self.styles, self.variables, prog=self.prog, scope=scope)
        resolved_cmd = interp.interpolate(enabled_if)
        proc = subprocess.run(
            resolved_cmd, shell=True, check=False, capture_output=True
        )
        if proc.returncode != 0:  # noqa: SIM103
            # the shell command returned a non-zero exit code
            # and this scope should therefore be disabled
            return False
        return True
