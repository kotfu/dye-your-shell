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
"""class for storing and processing a scope"""

import contextlib
import subprocess

import jinja2
import rich

from .agents import AgentBase
from .exceptions import DyeError, DyeSyntaxError
from .filters import jinja_filters


class Scope:
    """represent a scope

    This class handles stuff that is the same for all scopes,
    no matter what the agent for that scope is. This includes:

        - making sure an agent is defined
        - instantiating the agent class
        - processing templates (colors, styles, variables) in the scope
        - processing styles in the scope

    When you want to run this scope, ie have the agent generate output
    based on the scope, you should do:

        scope.run_agent()
    """

    @classmethod
    def extract(cls, pattern=None, name=None):
        """Extract a scope object from a pattern object"""
        if pattern and name:
            scope = cls()
            scope._process(pattern, name)
            return scope

        return None

    #
    # initialization and properties
    #
    def __init__(self):
        """Construct a new Scope object"""

        self.name = {}

        """A toml definition of the scope, which has had all templates processed"""
        self.definition = {}

        """The dictionary of style objects defined in this scope"""
        self.styles = {}

    def _process(self, pattern, name):
        """Process the scope definition

        this sets self.definition, which contains
        toml that has had all templates (i.e. colors, styles, variables)
        processed in all values

        it also sets self.styles, as a dict of style objects
        """
        try:
            scopedef = pattern.definition["scopes"][name]
        except KeyError as exc:
            raise DyeError(f"{name}: no such scope") from exc
        self.name = name

        env = jinja2.Environment()
        env.filters = jinja_filters()
        data = {}
        data["color"] = pattern.colors
        data["colors"] = pattern.colors
        data["style"] = pattern.styles
        data["styles"] = pattern.styles
        data["var"] = pattern.variables
        data["vars"] = pattern.variables
        data["variable"] = pattern.variables
        data["variables"] = pattern.variables
        env.globals = data

        def render_func(value):
            template = env.from_string(value)
            return template.render()

        self.definition = self._process_graph(scopedef, render_func)

        self._process_scope_styles()

    def _process_graph(self, dataset, render_func):
        """recursive function to crawl through a dictionary and
        call render_func for every nested dict and list item

        """
        result = {}
        for key, value in dataset.items():
            if isinstance(value, dict):
                result[key] = self._process_graph(value, render_func)
            elif isinstance(value, list):
                result[key] = map(render_func, value)
            elif isinstance(value, str):
                result[key] = render_func(value)
            else:
                # don't try and render non-string values
                result[key] = value
        return result

    def _process_scope_styles(self):
        """create a dictionary of style objects parsed from self.definition

        sets self.styles
        """
        try:
            raw_styles = self.definition["styles"]
        except (KeyError, TypeError):
            raw_styles = {}

        processed_styles = {}
        for name, styledef in raw_styles.items():
            processed_styles[name] = rich.style.Style.parse(styledef)

        self.styles = processed_styles

    def run_agent(self, comments=False):
        """
        returns output consisting of shell commands which must
        be sourced in the current shell in order to become active
        """
        try:
            agent_name = self.definition["agent"]
        except KeyError as exc:
            errmsg = f"scope '{self.name}' does not have an agent."
            raise DyeSyntaxError(errmsg) from exc

        try:
            # go get the apropriate class for the agent
            agent_cls = AgentBase.classmap[agent_name]
            # initialize the class with the scope (that's our self)
            agent = agent_cls(self)
        except KeyError as exc:
            raise DyeError(f"{agent_name}: unknown agent") from exc

        if self._enabled(comments):
            # run the agent, printing any shell commands it returns
            output = agent.run(comments)
            if output:
                print(output)

    def _enabled(self, comments=False):
        """Determine if the scope is enabled
        The default is that the scope is enabled

        returns whether this scope is enabled

        If can be disabled by any of these in the pattern file:

            enabled = false

        or:
            enabled_if = "{shell cmd}" returns a non-zero exit code

        if 'enabled = false' is present, then enabled_if is not checked

        May print output to be executed by the shell, may execute
        shell commands too
        """
        with contextlib.suppress(KeyError):
            enabled = self.definition["enabled"]
            if not isinstance(enabled, bool):
                raise DyeSyntaxError(
                    f"scope '{self.name}' requires 'enabled' to be true or false"
                )
            # this is authoritative, if it exists, ignore enabled_if below
            return enabled

        # no enabled directive, so we check for enabled_if
        try:
            enabled_if = self.definition["enabled_if"]
            if not enabled_if:
                # we have a key, but an empty value (aka command)
                # by rule we say it's enabled
                return True
        except KeyError:
            # no enabled_if key, so we must be enabled
            return True

        # if we get here we have something in enabled_if that
        # we need to go run
        proc = subprocess.run(enabled_if, shell=True, check=False, capture_output=True)
        if proc.returncode != 0:  # noqa: SIM103
            # the shell command returned a non-zero exit code
            # and this scope should therefore be disabled
            return False
        return True
