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
import os
import re

from .exceptions import ThemeError


class Interpolator:
    """Interpolate style and variable keywords"""

    def __init__(self, styles=None, variables=None, **msgdata):
        super().__init__()
        if styles is None:
            self.styles = {}
        else:
            self.styles = styles
        if variables is None:
            self.variables = {}
        else:
            self.variables = variables
        self.msgdata = msgdata

    def interpolate(self, text: str) -> str:
        "interpolate variables and styles in the given text"
        text = self.interpolate_variables(text)
        text = self.interpolate_environment(text)
        return self.interpolate_styles(text)

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
        #
        # (\\)? = match the backslash for group 1
        # (\{(var|variable): = open group 2, then match the opening brace
        #                      and either var or variable followed by a
        #                      colon in group 3
        # (.*?) = non-greedy variable name in group 4
        # \}) = the closing brace, escaped because } means something in
        #       a regex, and the closing paren for group 2
        newvalue = re.sub(r"(\\)?(\{(var|variable):(.*?)\})", tmpfunc, text)
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
        # match.group(3) is the literal 'var' or 'variable', we don't need that.
        # group 4 has the name of the variable
        varname = match.group(4)

        if backslash:
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            return f"{phrase}"

        try:
            value = self.variables[varname]
            if isinstance(value, bool):  # noqa: SIM108
                # toml booleans are all lower case, python are not
                # since the source toml is all lower case, we will
                # make the replacement be the same
                out = str(value).lower()
            else:
                out = str(value)
            return out
        except KeyError as exc:
            # we can't find the variable, which is an error
            raise ThemeError(
                f"{self.msgdata['prog']}: undefined variable '{varname}'"
                f" referenced in scope '{self.msgdata['scope']}"
            ) from exc

    def interpolate_environment(self, text: str) -> str:
        """interpolate environment variables in a passed value"""
        # this incantation gives us a callable function which is
        # really a method on our class, and which gets self
        # passed to the method just like any other method
        tmpfunc = functools.partial(self._env_subber)
        # this regex matches any of the following:
        #   {var:darkorange}
        #   {variable:yellow}
        #   \{variable:blue}
        # so we can replace it with a previously defined variable.
        #
        # match group 1 = backslash, if present
        # match group 2 = entire variable phrase
        # match group 3 = 'env' or 'environment'
        # match group 4 = name of the variable
        #
        # (\\)? = match the backslash for group 1
        # (\{(env|environment): = open group 2, then match the opening brace
        #                      and either var or variable followed by a
        #                      colon in group 3
        # (.*?) = non-greedy variable name in group 4
        # \}) = the closing brace, escaped because } means something in
        #       a regex, and the closing paren for group 2
        newvalue = re.sub(r"(\\)?(\{(env|environment):(.*?)\})", tmpfunc, text)
        return newvalue

    def _env_subber(self, match):
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
        # match.group(3) is the literal 'env' or 'environment', we don't need that.
        # group 4 contains the name of the environment variable
        varname = match.group(4)

        if backslash:  # noqa: SIM108
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            out = f"{phrase}"
        else:
            # get environment variable, with empty string as the default value
            # same as how bash works
            out = os.getenv(varname, "")
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
        #   {style:red:ansi_on}
        #   \{style:blue:hex}
        # so we can replace it with style information.
        #
        # match group 1 = backslash, if present
        # match group 2 = entire style/format phrase
        # match group 3 = name of the style (not the literal 'style:')
        # match group 4 = format
        #
        # (\\)? = match the backslash for group 1
        # (\{style:(.*?) = open group 2, then match {style:  with an
        #                  escaped { and whatever the style name is
        #                  (with a non-greedy match) in group 3
        # (?::(.*?))? = the optional format part
        # \}) = the closing brace, escaped because } means something in
        #       a regex, and the closing paren for group 2
        newvalue = re.sub(r"(\\)?(\{style:(.*?)(?::(.*?))?\})", tmpfunc, text)
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
        # this is the name of the style
        style_name = match.group(3)
        # the stuff after the colon but before the closing brace
        fmt = match.group(4)

        if backslash:
            # the only thing we replace is the backslash, the rest of it gets
            # passed through as is, which the regex conveniently has for us
            # in match group 2
            return f"{phrase}"

        try:
            style = self.styles[style_name]
        except KeyError as exc:
            raise ThemeError(
                f"{self.msgdata['prog']}: undefined style '{style_name}'"
                f" while processing scope '{self.msgdata['scope']}'"
            ) from exc

        if fmt in [None, "", "hex"]:
            # no format, or empty string format, or hex, the match with the hex code
            out = style.color.triplet.hex
        elif fmt == "hexnohash":
            # replace the match with the hex code without the hash
            out = style.color.triplet.hex.replace("#", "")
        elif fmt == "ansi_on":
            splitter = "-----"
            ansistring = style.render(splitter)
            out, _ = ansistring.split(splitter)
        elif fmt == "ansi_off":
            splitter = "-----"
            ansistring = style.render(splitter)
            _, out = ansistring.split(splitter)
        else:
            # an unknown format is an error
            raise ThemeError(
                f"{self.msgdata['prog']}: unknown style interpolation format"
                f" '{fmt}' while processing scope '{self.msgdata['scope']}'"
            )
        return out
