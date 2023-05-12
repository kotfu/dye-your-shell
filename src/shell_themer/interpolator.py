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
"""interpolators for variables and styles"""

import functools
import re

import rich.errors
import rich.style


class Interpolator:
    """Interpolate style and variable keywords"""

    def __init__(self, styles, variables):
        super().__init__()
        self.styles = styles
        self.variables = variables

    def value_of(self, variable):
        """return the value or contents of a variable

        performs variable interpolation at access time, not at
        parse time

        return None if variable is not defined
        """
        try:
            definedvalue = self.variables[variable]
            # we can only interpolate variables in string type values
            if isinstance(definedvalue, str):
                return self.interpolate(definedvalue)
            return definedvalue
        except KeyError:
            # variable not defined
            return None

    def interpolate(self, text):
        "interpolate variables and styles in the given text"
        newtext = self.interpolate_variables(text)
        newtext = self.interpolate_styles(newtext)
        return newtext

    def interpolate_variables(self, text: str) -> str:
        """interpolate variables in the passed value"""
        # this incantation gives us a callable function which is
        # really a method on our class, and which gets self
        # passed to the method just like any other method
        tmpfunc = functools.partial(self._var_subber)
        # this regex matches any of the following:
        #   {var:darkorange}
        #   {variable:yellow}
        #   \{variable:blue}
        # so we can replace it with a previously defined variable.
        #
        # match group 1 = backslash, if present
        # match group 2 = entire variable phrase
        # match group 3 = 'var' or 'variable'
        # match group 4 = name of the variable
        newvalue = re.sub(
            r"(\\)?(\{(var|variable):([^}:]*)(?::(.*))?\})", tmpfunc, text
        )
        return newvalue

    def _var_subber(self, match):
        """the replacement function called by re.sub() in variable_interpolate()

        this decides the replacement text for the matched regular expression

        the philosophy is to have the replacement string be exactly what was
        matched in the string, unless we the variable given exists and has a
        value, in which case we insert that value.
        """
        # the backslash to protect the brace, may or may not be present
        backslash = match.group(1)
        # the entire phrase, including the braces
        phrase = match.group(2)
        # match.group(3) is the literal 'var' or 'variable', we don't need that
        # the stuff after the colon but before the closing brace
        varname = match.group(4)

        if backslash:
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            out = f"{phrase}"
        else:
            value = self.value_of(varname)
            if value is None:
                # we can't find the variable, so don't do a replacement
                out = match.group(0)
            else:
                if isinstance(value, bool):
                    # toml booleans are all lower case, python are not
                    # since the source toml is all lower case, we will
                    # make the replacement be the same
                    out = str(value).lower()
                else:
                    out = str(value)
        return out

    def interpolate_styles(self, text: str) -> str:
        """interpolate styles in a passed value"""
        # this incantation gives us a callable function which is
        # really a method on our class, and which gets self
        # passed to the method just like any other method
        tmpfunc = functools.partial(self._style_subber)
        # this regex matches any of the following:
        #   {style:darkorange}
        #   {style:yellow:}
        #   \{style:blue:hex}
        # so we can replace it with style information.
        #
        # match group 1 = backslash, if present
        # match group 2 = entire style/format phrase
        # match group 3 = name of the style (not the literal 'style:')
        # match group 4 = format
        newvalue = re.sub(r"(\\)?(\{style:([^}:]*)(?::(.*))?\})", tmpfunc, text)
        return newvalue

    def _style_subber(self, match):
        """the replacement function called by re.sub()

        this decides the replacement text for the matched regular expression

        the philosophy is to have the replacement string be exactly what was
        matched in the string, unless we can successfully decode both the
        style and the format.
        """
        # the backslash to protect the brace, may or may not be present
        backslash = match.group(1)
        # the entire phrase, including the braces
        phrase = match.group(2)
        # the stuff after the opening brace but before the colon
        # this is the defition of the style
        styledef = match.group(3)
        # the stuff after the colon but before the closing brace
        fmt = match.group(4)

        if backslash:
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            out = f"{phrase}"
        else:
            try:
                style = self._get_style(styledef)
            except rich.errors.StyleSyntaxError:
                style = None

            if not style:
                # the style wasn't found, so don't do any replacement
                out = match.group(0)
            elif fmt in [None, "", "hex"]:
                # no format, or empty string format, or hex, the match with the hex code
                out = style.color.triplet.hex
            elif fmt == "hexnohash":
                # replace the match with the hex code without the hash
                out = style.color.triplet.hex.replace("#", "")
            else:
                # unknown format, so don't do any replacement
                out = phrase

        return out

    def _get_style(self, styledef):
        """convert a string into rich.style.Style object"""
        # first check if this definition is already in our list of styles
        try:
            style = self.styles[styledef]
        except KeyError:
            style = None
        # nope, parse the input as a style
        if not style:
            style = rich.style.Style.parse(styledef)
        return style
