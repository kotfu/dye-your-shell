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
# pylint: disable=protected-access, missing-function-docstring, redefined-outer-name
# pylint: disable=missing-module-docstring, unused-variable

import pytest
import rich.style

from shell_themer.interpolator import Interpolator
from shell_themer.parsers import StyleParser

INTERPOLATIONS = [
    ("{style:dark_orange}", "#ff6c1c"),
    ("{style:dark_orange:hex}", "#ff6c1c"),
    ("{style:dark_orange:hexnohash}", "ff6c1c"),
    # for an unknown format or style, don't do any replacement
    ("{style:current_line}", "{style:current_line}"),
    ("{style:dark_orange:unknown}", "{style:dark_orange:unknown}"),
    # we have to have the 'style' or 'variable' keyword, or
    # it all just gets passed through
    ("{dark_orange}", "{dark_orange}"),
    # escaped opening bracket means we should not interpolate
    (r"\{style:dark_orange}", "{style:dark_orange}"),
    # if you don't have matched brackets, or are missing a keyword
    # i.e. 'style:' or 'var:', don't expect the backslash
    # to be removed
    (r"\{ some other  things}", r"\{ some other  things}"),
    (r"\{escaped unmatched bracket", r"\{escaped unmatched bracket"),
    (r"\{notakeyword:something}", r"\{notakeyword:something}"),
    # both a variable and style interpolation in the same call
    ("{style:dark_orange} {var:someopts}", "#ff6c1c --option=fred -v"),
    ("", ""),
]

# TODO figure out if we could/should do some sort of end-to-end
# test on this. I moved this test from test_themer.py
# VARIABLE_INTERPOLATIONS = [
#     ("{variable:SomeVar} there", "Hello there"),
#     ("{variable:somevar} there", "{variable:somevar} there"),
#     ("It is {var:bool}.", "It is true."),
#     ("nothing to be done", "nothing to be done"),
#     ("fred='{var:empty}'", "fred=''"),
#     (r"\{variable:SomeVar} there", "{variable:SomeVar} there"),
#     ("I have {var:number} apples.", "I have 5 apples."),
#     ("count: {variable:another_var}", "count: one,two,three"),
# ]


# @pytest.mark.parametrize("value, newvalue", VARIABLE_INTERPOLATIONS)
# def test_variable_interpolate(thm, value, newvalue):
#     tomlstr = """
#         [variables]
#         SomeVar =  "Hello"
#         another_var = "one,two,three"
#         comment =  "#6272a4"
#         number = 5
#         bool = true
#         empty = ""
#     """
#     thm.loads(tomlstr)
#     assert thm.variable_interpolate(value) == newvalue


@pytest.mark.parametrize("text, resolved", INTERPOLATIONS)
def test_interpolate(text, resolved):
    variables = {"someopts": "--option=fred -v"}
    styles = {"dark_orange": rich.style.Style.parse("#ff6c1c")}
    interp = Interpolator(styles, variables)
    assert resolved == interp.interpolate(text)


STYLEPOLATIONS = [
    ("{style:dark_orange}", "#ff6c1c"),
    ("{style:dark_orange:hex}", "#ff6c1c"),
    ("{style:dark_orange:hexnohash}", "ff6c1c"),
    # multiple styles
    ("{style:dark_orange}-{style:dark_orange:hexnohash}", "#ff6c1c-ff6c1c"),
    # for an unknown format or style, don't do any replacement
    ("{style:current_line}", "{style:current_line}"),
    ("{style:dark_orange:unknown}", "{style:dark_orange:unknown}"),
    # we have to have the style keyword, or it all just gets passed through
    ("{dark_orange}", "{dark_orange}"),
    ("{variable:exists}", "{variable:exists}"),
    # escaped opening bracket means we should not interpolate
    (r"\{style:dark_orange}", "{style:dark_orange}"),
    # if you don't have matched brackets, or are missing the
    # literal 'style:' keyword, don't expect the backslash
    # to be removed.
    (r"\{ some other  things}", r"\{ some other  things}"),
    (r"\{escaped unmatched bracket", r"\{escaped unmatched bracket"),
    ("", ""),
]


@pytest.mark.parametrize("text, resolved", STYLEPOLATIONS)
def test_interpolate_styles(text, resolved):
    styles = {"dark_orange": rich.style.Style.parse("#ff6c1c")}
    # create a variable, so we can check that it doesn't get interpolated
    variables = {"exists": "yup"}
    interp = Interpolator(styles, variables)
    assert resolved == interp.interpolate_styles(text)


VARPOLATIONS = [
    ("{variable:green}", "{variable:green}"),
    ("{variable:someopts}", "--option=fred -v"),
    # multiple variables
    (
        "{---{variable:someopts}---{variable:someopts}}",
        "{-----option=fred -v-----option=fred -v}",
    ),
    # we have to have the 'variable:' keyword, or it all just gets passed through
    ("{someopts}", "{someopts}"),
    ("{style:foreground}", "{style:foreground}"),
    # escaped opening bracket means we should not interpolate
    (r"\{var:someopts}", "{var:someopts}"),
    # if you don't have matched brackets, or are missing the
    # literal 'variable:' keyword, don't expect the backslash
    # to be removed.
    (r"\{ some other  things}", r"\{ some other  things}"),
    (r"\{escaped unmatched bracket", r"\{escaped unmatched bracket"),
    ("", ""),
]


@pytest.mark.parametrize("text, resolved", VARPOLATIONS)
def test_interpolate_variables(text, resolved):
    variables = {"someopts": "--option=fred -v"}
    # create some styles so we can make sure they don't get interpolated
    raw_styles = {"foreground": "#dddddd"}
    sp = StyleParser(None, None)
    styles = sp.parse_dict(raw_styles)
    # create our interpolator
    interp = Interpolator(styles, variables)
    assert resolved == interp.interpolate_variables(text)
