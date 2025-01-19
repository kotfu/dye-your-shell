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

import jinja2
import tomlkit
from benedict import benedict

from .utils import merge_and_process_colors, merge_and_process_styles


class Theme:
    """load and parse a toml file into a theme object"""

    # class methods to create a new theme
    @classmethod
    def loads(cls, tomlstring=None):
        """Process a given string as a theme and return a new theme object"""
        if tomlstring:  # noqa: SIM108
            toparse = tomlstring
        else:
            # tomlkit can't parse None, so if we got it as the default
            # or if the caller pased None intentionally...
            toparse = ""
        theme = cls()
        theme.definition = benedict(tomlkit.loads(toparse))
        theme._process()
        return theme

    @classmethod
    def load(cls, fobj, filename=None):
        """Process a file object as a theme and return a new theme object

        Pass the optional filename to put in the .filename property
        of the returned theme object
        """
        theme = cls()
        theme.definition = benedict(tomlkit.load(fobj))
        theme.filename = filename
        theme._process()
        return theme

    #
    # initialization and properties
    #
    def __init__(self):
        """Construct a new Theme object"""

        # the raw toml definition of the theme
        self.definition = benedict()

        # the processed colors, it's a dict of strings
        self.colors = benedict()

        # the processed elements, it's a dict of rich.style.Style()
        self.styles = benedict()

        # a place to stash the file that the theme was loaded from
        # it's up to the caller/user to make sure this is set properly
        # defaults to None
        self.filename = None

    def __bool__(self):
        """Falsy if the definition is falsy, truthy if the definition is truthy"""
        return bool(self.definition)

    def _process(self):
        """process a newly loaded definition, including variables and styles

        this sets self.colors and self.styles
        """
        env = jinja2.Environment()

        try:
            raw_colors = benedict(self.definition["colors"])
        except KeyError:
            raw_colors = benedict()
        self.colors = benedict()
        merge_and_process_colors(self.colors, raw_colors, env)

        # process the elements, using the colors as variables
        # each element in should be a rich.Style() object
        try:
            raw_styles = benedict(self.definition["styles"])
        except KeyError:
            raw_styles = benedict()
        self.styles = benedict()
        merge_and_process_styles(self.styles, raw_styles, env, self.colors)
