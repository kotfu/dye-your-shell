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

import benedict
import jinja2
import rich
import tomlkit


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
        theme.definition = tomlkit.loads(toparse)
        theme._process()
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
        theme._process()
        return theme

    #
    # initialization and properties
    #
    def __init__(self):
        """Construct a new Theme object"""

        # the raw toml definition of the theme
        self.definition = {}

        # the processed colors, it's a dict of strings
        self.colors = {}

        # the processed elements, it's a dict of rich.style.Style()
        self.styles = {}

        # a place to stash the file that the theme was loaded from
        # it's up to the caller/user to make sure this is set properly
        # defaults to None
        self.filename = None

    def _process(self):
        """process a newly loaded definition, including variables and styles

        this sets self.colors and self.styles
        """
        env = jinja2.Environment()

        try:
            raw_colors = benedict.benedict(self.definition["colors"])
        except KeyError:
            raw_colors = benedict.benedict()
        self.colors = benedict.benedict()

        # we would use benedict.keypaths() but it sorts the keypaths,
        # and order is important to us. These two lines of code I stole
        # out of the soure for keypaths(), they are the ones right before
        # the .sort()
        kls = benedict.core.keylists(raw_colors)
        keylist = [".".join([f"{key}" for key in kl]) for kl in kls]

        # iterate over all the keys in raw_colors, processing and inserting
        # the values into self.colors
        for key in keylist:
            value = raw_colors[key]
            if isinstance(value, str):
                if value in self.colors:
                    # bare lookup so that foreground_low = "foreground" works
                    self.colors[key] = self.colors[value]
                else:
                    template = env.from_string(value)
                    self.colors[key] = template.render(
                        # this lets us do {{colors.foreground}} or {{color.foreground}}
                        colors=self.colors,
                        color=self.colors,
                    )
            else:
                self.colors[key] = value

        # process the elements, using the colors as variables
        # each element in should be a rich.Style() object
        try:
            raw_styles = self.definition["styles"]
        except KeyError:
            raw_styles = {}
        self.styles = {}
        for key, value in raw_styles.items():
            # do a bare lookup so that text_low = "text" works
            if value in self.styles:
                self.styles[key] = self.styles[value]
            else:
                template = env.from_string(value)
                # allow {{style.foreground}} or {{styles.foreground}}
                # or {{color.background}} or {{colors.background}}
                rendered = template.render(
                    color=self.colors,
                    colors=self.colors,
                    style=self.styles,
                    styles=self.styles,
                )
                self.styles[key] = rich.style.Style.parse(rendered)
