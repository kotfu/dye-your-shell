#
# Copyright (c) 2025 Jared Crapo
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


from dye.utils import deep_map


def render_func(value, newval):
    """callback used for testing deep_map()"""
    # only process strings
    if isinstance(value, str):
        return newval
    return value


def test_deep_map_onevalue():
    # can't mutate a string, so it should just come back with the old value
    old = "oldval"
    deep_map(old, render_func, "newvalue")
    assert old == "oldval"


def test_deep_map_nested_dicts():
    data = {"one": "oldval", "two": {"three": "oldval"}}
    deep_map(data, render_func, "fixed")
    assert data["two"]["three"] == "fixed"


def test_deep_map_nested_list():
    data = ["one", "two", {"three": "oldval", "four": "oldval"}]
    deep_map(data, render_func, "shiny")
    assert data[0] == "shiny"
    assert data[2]["four"] == "shiny"


def test_deep_map_empty_dict():
    data = {}
    deep_map(data, render_func, "gotime")
    assert data == {}


def test_deep_map_empty_list():
    data = []
    deep_map(data, render_func, "gotime")
    assert data == []
