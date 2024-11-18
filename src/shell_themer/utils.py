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


class AssertBool:
    """Mixin class containing a boolean assertion method

    :raises ThemeError: if the value is not boolean
    """

    def assert_bool(self, value, generator=None, **msgdata):
        """raise ThemeError if value is not a boolean

        msgdata is a dictionary of items used to create a useful
        error message.

        generator = the name of the generator that triggered the error
                    if not present, null, or empty, the error message
                    won't include which generator caused the error.
                    generator is optional
        prog = the name of the program, required
        scope = the name of the scope to include in the error message, required
        key = the key which must contain the true or false value, required
        """
        if not isinstance(value, bool):
            if generator:
                errmsg = (
                    f"{msgdata['prog']}: {generator} generator for"
                    f" scope '{msgdata['scope']}' requires '{msgdata['key']}'"
                    f" to be true or false"
                )
            else:
                errmsg = (
                    f"{msgdata['prog']}: scope '{msgdata['scope']}'"
                    f" requires '{msgdata['key']}' to be true or false"
                )
            raise ThemeError(errmsg)
