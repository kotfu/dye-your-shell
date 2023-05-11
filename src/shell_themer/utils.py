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
"""utility classes"""

from .exceptions import ThemeError
from .interpolator import Interpolator


class AssertBool:
    """Mixin class containing a boolean assertion method

    :raises ThemeError: if the value is not boolean
    """

    # TODO move self.prog, generator, scope, key into a msgdata dictionary
    def assert_bool(self, prog, value, generator, scope, key):
        if not isinstance(value, bool):
            if generator:
                errmsg = (
                    f"{prog}: {generator} generator for"
                    f" scope '{scope}' requires '{key}' to be true or false"
                )
            else:
                errmsg = f"{prog}: scope '{scope}' requires '{key}' to be true or false"
            raise ThemeError(errmsg)


class VariableGetter:
    """Mixin class with a method to get the value of a variable"""

    def value_of(varname, styles, variables):
        try:
            definedvalue = variables[varname]
            # we can only interpolate variables in string type values
            if isinstance(definedvalue, str):
                interp = Interpolator(styles, variables)
                return interp.interpolate(definedvalue)
            return definedvalue
        except KeyError:
            # variable not defined
            return None
