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
import rich
import tomlkit


class Theme:
    """load and parse a theme file into a theme object"""

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
        theme.definition = tomlkit.loads(toparse)
        theme._process_definition()
        return theme

    @classmethod
    def load(cls, fobj, filename=None):
        """Process a file object as a theme and return a new theme object

        Pass the optional filename to put in the .filename property
        of the returned theme object
        """
        theme = cls()
        theme.definition = tomlkit.load(fobj)
        theme.filename = filename
        theme._process_definition()
        return theme

    #
    # initialization and properties
    #
    def __init__(self):
        """Construct a new Theme object"""

        # the raw toml definition of the theme
        self.definition = {}

        # the processed palette
        self.palette = {}

        # the processed elements
        self.elements = {}

        # a place to stash the file that the theme was loaded from
        # it's up to the caller/user to make sure this is set properly
        # defaults to None
        self.filename = None

    def _process_definition(self):
        """process a newly loaded definition, including variables and styles

        this sets self.palette and self.elements
        """
        # get the palette, which is just a dict of variables
        # which can be used later
        try:
            self.palette = self.definition["palette"]
        except KeyError:
            self.palette = {}

        # process the elements, using the palette as variables
        # each element in should be a rich.Style() object
        env = jinja2.Environment()
        env.globals = self.palette
        try:
            raw_elements = self.definition["elements"]
        except KeyError:
            raw_elements = {}
        elements = {}
        for key, value in raw_elements.items():
            template = env.from_string(value)
            elements[key] = rich.style.Style.parse(template.render())
        self.elements = elements
