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

import os

import pytest
import rich.style

from shell_themer import ThemeError
from shell_themer.interpolator import Interpolator
from shell_themer.parsers import StyleParser

INTERPOLATIONS = [
    ("{style:dark_orange:hex}", "#ff6c1c"),
    ("{env:THEMER_COLORS} {variable:password}", "text=#f0f0f0 newenglandclamchowder"),
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
    # nested and complex versions
    ("{style:dark_orange} {var:someopts}", "#ff6c1c --option=fred -v"),
    ("HOME='{var:nested}'", "HOME='/home/ace'"),
    # booleans and numbers
    ("it's {var:bool}", "it's true"),
    ("countdown in {var:number}", "countdown in 5"),
    # empty is empty
    ("{var:empty}", ""),
    ("", ""),
]


@pytest.mark.parametrize("text, resolved", INTERPOLATIONS)
def test_interpolate(mocker, text, resolved):
    variables = {
        "password": "newenglandclamchowder",
        "someopts": "--option=fred -v",
        "nested": "{env:HOME}",
        "number": 5,
        "bool": True,
        "empty": "",
    }
    styles = {"dark_orange": rich.style.Style.parse("#ff6c1c")}
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"THEMER_COLORS": "text=#f0f0f0"})
    mocker.patch.dict(os.environ, {"HOME": "/home/ace"})
    interp = Interpolator(styles, variables)
    assert resolved == interp.interpolate(text)


STYLEPOLATIONS = [
    ("{style:dark_orange}", "#ff6c1c"),
    ("{style:dark_orange:hex}", "#ff6c1c"),
    ("{style:dark_orange:hexnohash}", "ff6c1c"),
    ("{style:dark_orange:ansi_on}", "\x1b[38;2;255;108;28m"),
    ("{style:dark_orange:ansi_off}", "\x1b[0m"),
    # multiple styles
    ("{style:dark_orange}-{style:dark_orange:hexnohash}", "#ff6c1c-ff6c1c"),
    # we have to have the style keyword, or it all just gets passed through
    ("{dark_orange}", "{dark_orange}"),
    # even though the variable is defined, we shouldn't replace it because
    # we are only going to interpolate styles
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
    interp = Interpolator(styles, variables, prog="theprog", scope="thescope")
    assert resolved == interp.interpolate_styles(text)


STYLE_ERRORS = [
    # unknown style
    "{style:text}",
    # unknown format
    "{style:dark_orange:unknownformat}",
]


@pytest.mark.parametrize("text", STYLE_ERRORS)
def test_interpolate_unknown_style(text):
    styles = {"dark_orange": rich.style.Style.parse("#ff6c1c")}
    # create a variable, so we can check that it doesn't get interpolated
    variables = {"exists": "yup"}
    interp = Interpolator(styles, variables, prog="theprog", scope="thescope")
    with pytest.raises(ThemeError):
        interp.interpolate_styles(text)


VARPOLATIONS = [
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
    # try interpolating numbers
    ("size {variable:size}", "size 5"),
    ("lets {variable:doit}", "lets true"),
    # empty should yield empty
    ("", ""),
]


@pytest.mark.parametrize("text, resolved", VARPOLATIONS)
def test_interpolate_variables(text, resolved):
    variables = {
        "someopts": "--option=fred -v",
        "size": 5,
        "doit": True,
    }
    # create some styles so we can make sure they don't get interpolated
    raw_styles = {"foreground": "#dddddd"}
    parser = StyleParser(None, None)
    styles = parser.parse_dict(raw_styles)
    # create our interpolator
    interp = Interpolator(styles, variables)
    assert resolved == interp.interpolate_variables(text)


def test_interpolate_unknown_variable():
    interp = Interpolator(None, None, prog="theprog", scope="thescope")
    with pytest.raises(ThemeError):
        interp.interpolate_variables("{var:one}")


ENVPOLATIONS = [
    ("{env:HOME}", "/home/ace"),
    ("say >{environment:NOTSET}<", "say ><"),
    (r"backslashed \{env:THEMER_COLORS}", "backslashed {env:THEMER_COLORS}"),
]


@pytest.mark.parametrize("text, resolved", ENVPOLATIONS)
def test_interpolate_environment(mocker, text, resolved):
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch.dict(os.environ, {"THEMER_COLORS": "text=#f0f0f0"})
    mocker.patch.dict(os.environ, {"HOME": "/home/ace"})
    interp = Interpolator(None, None)
    assert resolved == interp.interpolate_environment(text)
