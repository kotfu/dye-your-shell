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
import rich.errors
import rich.style

from dye import DyeError


#
# test style and variable processing on initialization
#
def test_process_definition(theme):
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
        yellow =  "#f1fa8c"

        [variables]
        capture.somevar = "printf '%s' {var:replace}"
        secondhalf = "5555"
        replace = "{var:secondhalf}"
        firsthalf = "fred"
        myred = "{var:firsthalf}{variable:secondhalf}"
        igreen = "{style:green:fghexnohash}"
        capture.anothervar = "printf '%s' myvalue"
    """
    theme.loads(tomlstr)
    # check the styles
    assert isinstance(theme.styles, dict)
    assert isinstance(theme.styles["cyan"], rich.style.Style)
    assert theme.styles["cyan"].color.name == "#8be9fd"
    assert theme.styles["yellow"].color.name == "#f1fa8c"
    assert len(theme.styles) == 10
    # check the variables
    assert len(theme.variables) == 7
    # capture doesn't interpolate variables
    assert theme.variables["somevar"] == "{var:replace}"
    # make sure capture variable actually captures
    assert theme.variables["anothervar"] == "myvalue"
    # styles interpolate into variables
    assert theme.variables["igreen"] == "50fa7b"
    # variables interpolate into variables
    assert theme.variables["replace"] == "5555"
    assert theme.variables["myred"] == "fred5555"


def test_process_definition_duplicate_variables(theme):
    tomlstr = """
        [variables]
        capture.thevar = "printf '%s' thevalue"
        thevar = "fred"
    """
    with pytest.raises(DyeError):
        theme.loads(tomlstr)


def test_process_definition_capture_error(theme):
    # the extra f in printff should return a non-zero
    # exit code, which is an error
    tomlstr = """
        [variables]
        capture.thevar = "printff '%s' thevalue"
    """
    with pytest.raises(DyeError):
        theme.loads(tomlstr)


def test_process_definition_undefined_variable(theme):
    tomlstr = """
        [variables]
        one = "{var:two}"
    """
    with pytest.raises(DyeError):
        theme.loads(tomlstr)


# TODO this should test the init in GeneratorBase which sets scope_styles
# def test_styles_from(thm):
#     tomlstr = """
#         [styles]
#         background =  "#282a36"
#         foreground =  "#f8f8f2"
#         current_line =  "#f8f8f2 on #44475a"
#         comment =  "#6272a4"
#         cyan =  "#8be9fd"
#         green =  "#50fa7b"
#         orange =  "#ffb86c"
#         pink =  "#ff79c6"
#         purple =  "#bd93f9"
#         red =  "#ff5555"
#         yellow =  "#f1fa8c"

#         [scope.iterm]
#         generator = "iterm"
#         style.foreground = "foreground"
#         style.background = "background"

#         [scope.fzf]
#         generator = "fzf"

#         # attributes specific to fzf
#         environment_variable = "FZF_DEFAULT_OPTS"

#         # command line options
#         opt.--prompt = ">"
#         opt.--border = "single"
#         opt.--pointer = "•"
#         opt.--info = "hidden"
#         opt.--no-sort = true
#         opt."+i" = true

#         # styles
#         style.text = "foreground"
#         style.label = "green"
#         style.border = "orange"
#         style.selected = "current_line"
#         style.prompt = "green"
#         style.indicator = "cyan"
#         style.match = "pink"
#         style.localstyle = "green on black"
#     """
#     thm.loads(tomlstr)
#     scopedef = thm.scopedef_for("fzf")
#     styles = thm.styles_from(scopedef)
#     assert isinstance(styles, dict)
#     assert len(styles) == 8
#     assert "indicator" in styles.keys()
#     assert isinstance(styles["localstyle"], rich.style.Style)
#     style = styles["selected"]
#     assert style.color.name == "#f8f8f2"
#     assert style.bgcolor.name == "#44475a"


# TODO I don't think we need to test this, as long as we test the
# init() method of GeneratorBase
# def test_styles_from_unknown(thm):
#     tomlstr = """
#         [scope.iterm]
#         generator = "iterm"
#         style.foreground = "foreground"
#         style.background = "background"
#     """
#     thm.loads(tomlstr)
#     scopedef = thm.scopedef_for("unknown")
#     styles = thm.styles_from(scopedef)
#     assert isinstance(styles, dict)
#     assert styles == {}


#
# test variable related methods, including interpolation
#


#
# test scope, parsing, and validation methods
#
def test_scopedef(theme):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    theme.loads(tomlstr)
    scopedef = theme.scopedef_for("iterm")
    assert isinstance(scopedef, dict)
    assert scopedef["agent"] == "iterm"
    assert len(scopedef) == 2
    # TODO this should be tested on the GeneratorBase, not here
    # styles = thm.styles_from(scopedef)
    # assert len(styles) == 2
    # assert isinstance(styles["foreground"], rich.style.Style)


def test_scopedef_notfound(theme):
    tomlstr = """
        [scope.iterm]
        agent = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    theme.loads(tomlstr)
    scopedef = theme.scopedef_for("notfound")
    assert isinstance(scopedef, dict)
    assert scopedef == {}


def test_has_scope(theme):
    tomlstr = """
        [scope.qqq]
        agent = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    theme.loads(tomlstr)
    assert theme.has_scope("qqq")
    assert not theme.has_scope("fred")


#
# test dye_dir() property
#
def test_dye_dir_environment_variable(dye, mocker, tmp_path):
    mocker.patch.dict(os.environ, {"DYE_DIR": str(tmp_path)})
    # dye_dir should be a Path object
    assert dye.dye_dir == tmp_path


def test_dye_dir_no_environment_variable(dye, mocker):
    # ensure no DYE_DIR environment variable exists
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(DyeError):
        _ = dye.dye_dir


def test_dye_dir_invalid_directory(dye, mocker, tmp_path):
    invalid = tmp_path / "doesntexist"
    mocker.patch.dict(os.environ, {"DYE_DIR": str(invalid)})
    with pytest.raises(DyeError):
        _ = dye.dye_dir


#
# test all the variations of load_from_args()
#
def test_load_from_args_no_theme(dye, mocker):
    # we need empty args, and empty environment, and with
    # all of this empty, we should get an exception
    mocker.patch.dict(os.environ, {}, clear=True)
    args = argparse.Namespace()
    args.file = None
    args.theme = None
    with pytest.raises(DyeError):
        dye.load_from_args(args)


def test_load_from_args_filename(dye, mocker, tmp_path):
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

    dye.load_from_args(args)
    assert dye.theme.definition
    assert dye.theme.styles


def test_load_from_args_invalid_filename(dye, mocker, tmp_path):
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
        dye.load_from_args(args)


def test_load_from_args_env(dye, mocker, tmp_path):
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

    dye.load_from_args(args)
    assert dye.theme.definition
    assert dye.theme.styles


def test_load_from_args_env_invalid(dye, mocker, tmp_path):
    # a theme file in the environment variable which doesn't exist
    # should raise an exception
    themefile = tmp_path / "doesntexist.toml"
    mocker.patch.dict(os.environ, {"THEME_FILE": str(themefile)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = None

    with pytest.raises(FileNotFoundError):
        dye.load_from_args(args)


def test_load_from_args_theme_file(dye, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    themefile = tmp_path / "themefile.toml"
    tomlstr = """
        [styles]
        text = "#ffcc00 on #003322"
    """
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(tomlstr)

    mocker.patch.dict(os.environ, {"DYE_DIR": str(tmp_path)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = "themefile.toml"

    dye.load_from_args(args)
    assert dye.theme.definition
    assert dye.theme.styles


def test_load_from_args_theme_file_invalid(dye, mocker, tmp_path):
    # we have a valid theme dir, but we are going to give
    # a filename with extension as the theme arguemtn
    # but that filename won't exist
    mocker.patch.dict(os.environ, {"DYE_DIR": str(tmp_path)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = "notfound.toml"

    with pytest.raises(DyeError):
        dye.load_from_args(args)


def test_load_from_args_theme_name(dye, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    themefile = tmp_path / "themefile.toml"
    tomlstr = """
        [styles]
        text = "#ffcc00 on #003322"
    """
    with open(themefile, "w", encoding="utf8") as fvar:
        fvar.write(tomlstr)

    mocker.patch.dict(os.environ, {"DYE_DIR": str(tmp_path)}, clear=True)

    args = argparse.Namespace()
    args.file = None
    args.theme = "themefile"

    dye.load_from_args(args)
    assert dye.theme.definition
    assert dye.theme.styles


#
# test loads() method
#
def test_loads_empty(theme):
    theme.loads("")
    assert isinstance(theme.definition, dict)
    assert theme.definition == {}
    assert isinstance(theme.styles, dict)
    assert theme.styles == {}
