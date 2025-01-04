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
# pylint: disable=protected-access, missing-function-docstring, redefined-outer-name
# pylint: disable=missing-module-docstring, unused-variable

import pytest

from shell_themer.exceptions import ThemeError
from shell_themer.utils import AssertBool

BOOL_TESTS = [
    (True, True),
    (False, True),
    ("something", False),
    (0, False),
    (1, False),
    (0.5, False),
]


@pytest.mark.parametrize("val, expected", BOOL_TESTS)
def test_assert_bool(val, expected):
    asserter = AssertBool()
    if expected:
        asserter.assert_bool(
            val, key="val", prog="prog", generator="generator", scope="scope"
        )
    else:
        with pytest.raises(ThemeError):
            asserter.assert_bool(
                val, key="val", prog="prog", geneartor="generator", scope="scope"
            )
