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

import argparse
import os

import pytest
import rich.style
import rich.errors

from shell_themer import ThemeError


#
# test style parsing
#
def test_get_style_plain(thm):
    style = thm.get_style("#aaff00")
    assert isinstance(style, rich.style.Style)
    assert style.color.name == "#aaff00"


def test_get_style_complex(thm):
    style = thm.get_style("bold white on red")
    assert isinstance(style, rich.style.Style)
    assert style.bold is True
    assert style.color.name == "white"
    assert style.bgcolor.name == "red"


def test_get_style_invalid(thm):
    with pytest.raises(rich.errors.StyleSyntaxError):
        _ = thm.get_style("not a valid style")


def test_get_style_interpolation(thm):
    tomlstr = """
        [variables]
        qyellow = "#ffff00"

        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"
        current_line =  "#f8f8f2 on #44475a"
        warning = "{var:qyellow}"
    """
    thm.loads(tomlstr)
    style = thm.get_style("current_line")
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"
    style = thm.get_style("warning")
    assert style.color.name == "#ffff00"


def test_process_definition(thm):
    tomlstr = """
        [variables]
        replace = "{var:secondhalf}"
        firsthalf = "#ff"
        secondhalf = "5555"
        myred = "{var:firsthalf}{variable:secondhalf}"
        igreen = "{style:green}"

        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"
        current_line =  "#f8f8f2 on #44475a"
        comment =  "#6272a4"
        cyan =  "#8be9fd"
        green =  "#50fa7b"
        orange =  "#ffb86c"
        pink =  "#ff79c6"
        purple =  "#bd93f9"
        red =  "{var:myred}"
        yellow =  "#f1fa8c"

        [scope.ls]
        # set some environment variables
        environment.unset = ["SOMEVAR", "ANOTHERVAR"]
        environment.export.LS_COLORS = "ace ventura"
    """
    thm.loads(tomlstr)
    assert isinstance(thm.styles, dict)
    assert isinstance(thm.styles["cyan"], rich.style.Style)
    assert thm.styles["cyan"].color.name == "#8be9fd"
    assert thm.styles["yellow"].color.name == "#f1fa8c"
    # check an interpolated variable in a style
    assert thm.styles["red"].color.name == "#ff5555"
    # check the variable interpolation
    assert thm.value_of("replace") == "5555"
    assert thm.value_of("myred") == "#ff5555"
    # check style interpolation in variables
    assert thm.value_of("igreen") == "#50fa7b"


def test_styles_from(thm):
    tomlstr = """
        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"
        current_line =  "#f8f8f2 on #44475a"
        comment =  "#6272a4"
        cyan =  "#8be9fd"
        green =  "#50fa7b"
        orange =  "#ffb86c"
        pink =  "#ff79c6"
        purple =  "#bd93f9"
        red =  "#ff5555"
        yellow =  "#f1fa8c"

        [scope.iterm]
        generator = "iterm"
        style.foreground = "foreground"
        style.background = "background"

        [scope.fzf]
        generator = "fzf"

        # attributes specific to fzf
        environment_variable = "FZF_DEFAULT_OPTS"

        # command line options
        opt.--prompt = ">"
        opt.--border = "single"
        opt.--pointer = "•"
        opt.--info = "hidden"
        opt.--no-sort = true
        opt."+i" = true

        # styles
        style.text = "foreground"
        style.label = "green"
        style.border = "orange"
        style.selected = "current_line"
        style.prompt = "green"
        style.indicator = "cyan"
        style.match = "pink"
        style.localstyle = "green on black"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("fzf")
    styles = thm.styles_from(scopedef)
    assert isinstance(styles, dict)
    assert len(styles) == 8
    assert "indicator" in styles.keys()
    assert isinstance(styles["localstyle"], rich.style.Style)
    style = styles["selected"]
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


def test_styles_from_unknown(thm):
    tomlstr = """
        [scope.iterm]
        generator = "iterm"
        style.foreground = "foreground"
        style.background = "background"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("unknown")
    styles = thm.styles_from(scopedef)
    assert isinstance(styles, dict)
    assert styles == {}


#
# test variable related methods, including interpolation
#
VARIABLES = [
    ("SomeVar", "Hello"),
    ("another_var", "one,two,three"),
    ("comment", "#6272a4"),
    ("empty", ""),
    ("number", 5),
    ("bool", True),
    ("notdefined", None),
    ("text", "#6272a4 on #002200"),
    # make sure we interpolate a style into a variable
    ("astyle", "00ff00"),
]


@pytest.mark.parametrize("variable, value", VARIABLES)
def test_value_of(thm, variable, value):
    tomlstr = """
        [variables]
        SomeVar =  "Hello"
        another_var = "one,two,three"
        comment =  "#6272a4"
        background = "#002200"
        number = 5
        bool = true
        empty = ""
        text = "{var:comment} on {variable:background}"
        astyle = "{style:green:hexnohash}"

        [styles]
        green = "#00ff00"
    """
    thm.loads(tomlstr)
    assert thm.value_of(variable) == value


VARIABLE_INTERPOLATIONS = [
    ("{variable:SomeVar} there", "Hello there"),
    ("{variable:somevar} there", "{variable:somevar} there"),
    ("It is {var:bool}.", "It is true."),
    ("nothing to be done", "nothing to be done"),
    ("fred='{var:empty}'", "fred=''"),
    (r"\{variable:SomeVar} there", "{variable:SomeVar} there"),
    ("I have {var:number} apples.", "I have 5 apples."),
    ("count: {variable:another_var}", "count: one,two,three"),
]


@pytest.mark.parametrize("value, newvalue", VARIABLE_INTERPOLATIONS)
def test_variable_interpolate(thm, value, newvalue):
    tomlstr = """
        [variables]
        SomeVar =  "Hello"
        another_var = "one,two,three"
        comment =  "#6272a4"
        number = 5
        bool = true
        empty = ""
    """
    thm.loads(tomlstr)
    assert thm.variable_interpolate(value) == newvalue


#
# test scope, parsing, and validation methods
#
def test_scopedef(thm):
    tomlstr = """
        [scope.iterm]
        generator = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("iterm")
    assert isinstance(scopedef, dict)
    assert scopedef["generator"] == "iterm"
    assert len(scopedef) == 2
    styles = thm.styles_from(scopedef)
    assert len(styles) == 2
    assert isinstance(styles["foreground"], rich.style.Style)


def test_scopedef_notfound(thm):
    tomlstr = """
        [scope.iterm]
        generator = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    thm.loads(tomlstr)
    scopedef = thm.scopedef_for("notfound")
    assert isinstance(scopedef, dict)
    assert scopedef == {}


def test_has_scope(thm):
    tomlstr = """
        [scope.qqq]
        generator = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    thm.loads(tomlstr)
    assert thm.has_scope("qqq")
    assert not thm.has_scope("fred")


BOOL_TESTS = [
    (True, True),
    (False, True),
    ("something", False),
    (0, False),
    (1, False),
    (0.5, False),
]


@pytest.mark.parametrize("val, expected", BOOL_TESTS)
def test_assert_bool(thm, val, expected):
    if expected:
        thm._assert_bool(val, "generator", "scope", "key")
    else:
        with pytest.raises(ThemeError):
            thm._assert_bool(val, "generator", "scope", "key")


#
# test theme_dir() property
#
def test_theme_dir_environment_variable(thm, mocker, tmp_path):
    mocker.patch.dict(os.environ, {"THEME_DIR": str(tmp_path)})
    # theme_dir should be a Path object
    assert thm.theme_dir == tmp_path


def test_theme_dir_no_environment_variable(thm, mocker):
    # ensure no THEME_DIR environment variable exists
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(ThemeError):
        _ = thm.theme_dir


def test_theme_dir_invalid_directory(thm, mocker, tmp_path):
    invalid = tmp_path / "doesntexist"
    mocker.patch.dict(os.environ, {"THEME_DIR": str(invalid)})
    with pytest.raises(ThemeError):
        _ = thm.theme_dir


#
# test all the variations of load_from_args()
#
def test_load_from_args_no_theme(thm, mocker):
    # we need empty args, and empty environment, and with
    # all of this empty, we should get an exception
    mocker.patch.dict(os.environ, {}, clear=True)
    args = argparse.Namespace()
    args.file = None
    args.theme = None
    with pytest.raises(ThemeError):
        thm.load_from_args(args)


def test_load_from_args_filename(thm, mocker, tmp_path):
    # give a bogus theme file in the environment, which should be
    # ignored because the filename in the arguments should take
    # precendence
    mocker.patch.dict(os.environ, {"THEME_FILE": "nosuchfile"}, clear=True)

    # go write a theme file that we can actually open
    themefile = tmp_path / "sometheme.toml"
    toml = """
    [styles]
    text = "#ffcc00 on #003322"
    """
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(toml)

    args = argparse.Namespace()
    args.file = str(themefile)
    args.theme = None

    thm.load_from_args(args)
    assert thm.definition
    assert thm.styles


def test_load_from_args_invalid_filename(thm, mocker, tmp_path):
    # give a real theme file in the environment, which should be
    # ignored because the filename in the arguments should take
    # precendence, this should generate an error because we
    # specified a file which could not be opened

    # go write a theme file that we can actually open
    envfile = tmp_path / "sometheme.toml"
    with open(envfile, "w", encoding="utf8") as fvar:
        fvar.write("# an empty toml theme file")
    mocker.patch.dict(os.environ, {"THEME_FILE": str(envfile)}, clear=True)

    themefile = tmp_path / "doesntexist.toml"
    args = argparse.Namespace()
    args.file = str(themefile)
    args.theme = None

    with pytest.raises(FileNotFoundError):
        thm.load_from_args(args)


def test_load_from_args_env(thm, mocker, tmp_path):
    # go write a theme file that we can actually open
    themefile = tmp_path / "sometheme.toml"
    tomlstr = """
        [styles]
        text = "#ffcc00 on #003322"
    """
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(tomlstr)

    mocker.patch.dict(os.environ, {"THEME_FILE": str(themefile)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = None

    thm.load_from_args(args)
    assert thm.definition
    assert thm.styles


def test_load_from_args_env_invalid(thm, mocker, tmp_path):
    # a theme file in the environment variable which doesn't exist
    # should raise an exception
    themefile = tmp_path / "doesntexist.toml"
    mocker.patch.dict(os.environ, {"THEME_FILE": str(themefile)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = None

    with pytest.raises(FileNotFoundError):
        thm.load_from_args(args)


def test_load_from_args_theme_file(thm, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    themefile = tmp_path / "themefile.toml"
    tomlstr = """
        [styles]
        text = "#ffcc00 on #003322"
    """
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(tomlstr)

    mocker.patch.dict(os.environ, {"THEME_DIR": str(tmp_path)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = "themefile.toml"

    thm.load_from_args(args)
    assert thm.definition
    assert thm.styles


def test_load_from_args_theme_file_invalid(thm, mocker, tmp_path):
    # we have a valid theme dir, but we are going to give
    # a filename with extension as the theme arguemtn
    # but that filename won't exist
    mocker.patch.dict(os.environ, {"THEME_DIR": str(tmp_path)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = "notfound.toml"

    with pytest.raises(ThemeError):
        thm.load_from_args(args)


def test_load_from_args_theme_name(thm, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    themefile = tmp_path / "themefile.toml"
    tomlstr = """
        [styles]
        text = "#ffcc00 on #003322"
    """
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(tomlstr)

    mocker.patch.dict(os.environ, {"THEME_DIR": str(tmp_path)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = "themefile"

    thm.load_from_args(args)
    assert thm.definition
    assert thm.styles


#
# test loads() method
#
def test_loads_empty(thm):
    thm.loads("")
    assert isinstance(thm.definition, dict)
    assert thm.definition == {}
    assert isinstance(thm.styles, dict)
    assert thm.styles == {}
