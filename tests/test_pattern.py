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
import rich.errors
import rich.style
import tomlkit

from dye.exceptions import DyeError, DyeSyntaxError
from dye.pattern import Pattern
from dye.scope import Scope
from dye.theme import Theme
from dye.utils import DefinitionSource

SAMPLE_THEME = """
[colors]
foreground = "#f8f8f2"
foreground_high = "foreground"
foreground_medium = "foreground"
foreground_low = "foreground"

triad.first = "#aaaaaa"
triad.second = "#bbbbbb"
triad.third = "#cccccc"

[styles]
themeonly = "{{color.foreground}} on #393b47"
foreground = "{{ color.foreground }}"
"""

SAMPLE_PATTERN = """
description = "Oxygen is a pattern with lots of space"
type = "dark"
version = "2.0"

requires_theme = "reqtheme"
prevent_themes = true

[colors]
pattern_purple =  "#bd93f8"
pattern_yellow =  "#f1fa8b"
notyet =  "{{ colors.yellow }}"

foreground =  "#e9e9e3"
background =  "#282a36"

foreground_unknown = "{{ colors.unknown }}"

background_high = "{{ colors.background }}"
background_medium = "{{ color.background }}"
background_low = "background"
background_double1 = "{{ color.background_low }}"
background_double2 = "background_medium"

yellow = "#e2eb9c"

triad.second = "#dd2222"

tetrad.first = "#ff1111"
tetrad.second = "#ff2222"
tetrad.third = "foreground_low"
tetrad.fourth = "{{ color.pattern_purple }}"
tetrad.fifth = "{{ colors.triad.third }}"

[styles]
notyet = "{{ styles.text }}"
foreground = "{{ color.foreground }}"
text = "bold {{ colors.foreground }} on {{ colors.background }}"
text_high = "{{ styles.text }}"
text_medium = "{{ style.text }}"
text_low = "text"
text_double1 = "{{ style.text_low }}"
text_double2 = "text_medium"
text_colorref = "{{ color.foreground_medium }}"
color1 = "#ff79c6"
color2 = "{{ colors.unknown }}"
color3 = "{{ style.unknown }}"
color4 = ""

pattern_text = '#cccccc on #ffffff'
pattern_text_high = '#000000 on #ffffff'
pattern_text_low = '#999999 on #ffffff'
pattern_yellow = "{{ colors.pattern_yellow }}"

triad_sty.first = "{{ colors.triad.first }}"
triad_sty.second = "pattern_text"
triad_sty.third = "{{ style.themeonly }}"

[variables]
capture.somevar = "printf '%s' jojo"
secondhalf = "5555"
replace = "{{variables.secondhalf}}"
firsthalf = "fred"
myred = "{{variables.firsthalf}}{{variables.secondhalf}}"
v_yellow = "{{styles.pattern_yellow|fg_hex_no_hash}}"
capture.anothervar = "printf '%s' {{colors.pattern_purple}}"

[scopes.iterm]
agent = "iterm"
cursor = "block"

[scopes.nocolor]
agent = "environment_variables"
export.NO_COLOR = "true"

[scopes.shell]
agent = "shell"
is_enabled = false
command.dontrun = "echo qqq"
"""


@pytest.fixture
def sthm():
    """the sample theme"""
    return Theme.loads(SAMPLE_THEME)


@pytest.fixture
def spat():
    """the sample pattern without loading the theme"""
    pattern = Pattern.loads(SAMPLE_PATTERN)
    return pattern


@pytest.fixture
def sthmpat():
    """the sample pattern with the sample theme merged into it"""
    theme = Theme.loads(SAMPLE_THEME)
    pattern = Pattern.loads(SAMPLE_PATTERN, theme)
    return pattern


#
# test dunders
#
def test_truthy1(spat):
    assert spat


def test_truthy2(sthmpat):
    assert sthmpat


def test_falsy1():
    assert not Pattern()


def test_falsy2():
    assert not Pattern.loads("")


def test_falsy3():
    assert not Pattern.loads(None)


#
# make sure load() and loads() work properly
#
def test_load(tmp_path):
    # def test_load_from_args_theme_name(dye, mocker, tmp_path):
    # give a theme name, but the full name including the .toml
    patternfile = tmp_path / "pattern.toml"
    with open(patternfile, "w", encoding="utf8") as fvar:
        fvar.write(SAMPLE_PATTERN)

    with open(patternfile, encoding="utf8") as fvar:
        pat = Pattern.load(fvar)
        assert pat.definition


def test_loads(spat):
    assert isinstance(spat.definition, dict)
    assert spat.definition


def test_loads_empty():
    pat = Pattern.loads("")
    assert pat.definition == {}


def test_loads_none():
    pat = Pattern.loads(None)
    assert pat.definition == {}


def test_loads_colors(spat):
    assert isinstance(spat.colors, dict)
    assert isinstance(spat.colors["pattern_purple"], str)
    assert spat.colors["pattern_purple"] == "#bd93f8"


def test_loads_styles(spat):
    assert isinstance(spat.styles, dict)
    assert isinstance(spat.styles["pattern_text"], rich.style.Style)
    assert isinstance(spat.styles["pattern_text_high"], rich.style.Style)


#
# test pattern metadata/properties
# these tests just ensure the data is extracted propertly
# from the toml
#
def test_description(spat):
    assert spat.description == "Oxygen is a pattern with lots of space"


def test_no_description():
    pattern_str = """prevent_themes = true"""
    pat = Pattern.loads(pattern_str)
    assert not pat.description


def test_type_not_defined():
    pattern_str = """
    [colors]
    foreground = "#d2d2d2"
    """
    pattern = Pattern.loads(pattern_str)
    assert not pattern.type


def test_type():
    pattern_str = """
    type = "dark"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.type == "dark"


def test_version_not_defined():
    pattern_str = """
    [colors]
    foreground = "#d2d2d2"
    """
    pattern = Pattern.loads(pattern_str)
    assert not pattern.version


def test_version():
    pattern_str = """
    version = "2.1"
    """
    pattern = Theme.loads(pattern_str)
    assert pattern.version == "2.1"


def test_prevent_themes():
    pattern_str = """prevent_themes = true"""
    pat = Pattern.loads(pattern_str)
    assert pat.prevent_themes


def test_prevent_themes_not_defined():
    pattern_str = """description = 'hi'"""
    pat = Pattern.loads(pattern_str)
    assert not pat.prevent_themes


def test_prevent_themes_not_boolean():
    pattern_str = "prevent_themes = 'nope'"
    with pytest.raises(DyeSyntaxError):
        Pattern.loads(pattern_str)


def test_requires_theme():
    pattern_str = """requires_theme = '/path/to/theme'"""
    pat = Pattern.loads(pattern_str)
    assert pat.requires_theme == "/path/to/theme"


def test_requires_theme_not_defined():
    pattern_str = """description = 'hi'"""
    pat = Pattern.loads(pattern_str)
    assert not pat.requires_theme


#
# test processing of colors
#
def test_color_pattern(sthmpat):
    """a color that is only defined in the pattern"""
    assert sthmpat.colors["background"] == "#282a36"


def test_color_theme(sthmpat):
    """a color that is only defined in the theme"""
    assert sthmpat.colors["foreground_high"] == "#f8f8f2"


def test_colors_must_be_strings():
    pattern_str = """
    [colors]
    background = 282
    """
    with pytest.raises(DyeSyntaxError):
        Pattern.loads(pattern_str)


def test_color_pattern_override_theme(sthm, spat, sthmpat):
    """a color defined in both pattern and theme, make sure pattern overrides"""
    assert sthm.colors["foreground"] == "#f8f8f2"
    # make sure we get the same answer whether we load the theme or not
    assert spat.colors["foreground"] == "#e9e9e3"
    assert sthmpat.colors["foreground"] == "#e9e9e3"


def test_colors_reference(sthmpat):
    assert sthmpat.colors["background_high"] == sthmpat.colors["background"]


def test_color_reference(sthmpat):
    assert sthmpat.colors["background_medium"] == sthmpat.colors["background"]


def test_colors_bare_reference(sthmpat):
    assert sthmpat.colors["background_low"] == sthmpat.colors["background"]


def test_colors_double1_reference(sthmpat):
    assert sthmpat.colors["background_double1"] == sthmpat.colors["background"]


def test_colors_double2_reference(sthmpat):
    assert sthmpat.colors["background_double2"] == sthmpat.colors["background"]


def test_colors_unknown_reference(sthmpat):
    assert sthmpat.colors["foreground_unknown"] == ""


def test_colors_load_order(sthmpat):
    assert sthmpat.colors["notyet"] == ""


def test_colors_subtable(sthmpat):
    assert sthmpat.colors["tetrad.first"] == "#ff1111"
    assert sthmpat.colors["tetrad.second"] == "#ff2222"


def test_colors_subtable_from_theme(sthmpat):
    assert sthmpat.colors["triad.first"] == "#aaaaaa"
    assert sthmpat.colors["triad.second"] == "#dd2222"
    assert sthmpat.colors["triad.third"] == "#cccccc"


def test_colors_subtable_reference1(sthmpat):
    # theme colors get resolved to values before pattern
    # colors do. Therefore, foreground_low for tetrad.third
    # resolves to #f8f8f2 not #e9e9e3
    assert sthmpat.colors["tetrad.third"] == "#f8f8f2"


def test_colors_subtable_reference2(sthmpat):
    assert sthmpat.colors["tetrad.fourth"] == sthmpat.colors["pattern_purple"]


def test_colors_subtable_reference3(sthmpat):
    assert sthmpat.colors["tetrad.fifth"] == "#cccccc"


#
# test processing of styles
#
def test_empty_pattern(sthm):
    pattern = Pattern.loads("", sthm)
    assert pattern.colors["foreground"]
    assert pattern.styles["themeonly"]


def test_style_pattern(spat):
    """defined only in the pattern, referencing colors
    only in the pattern"""
    assert spat.styles["text"].color.name == "#e9e9e3"
    assert spat.styles["text"].color.triplet.hex == "#e9e9e3"
    assert spat.styles["text"].bgcolor.name == "#282a36"
    assert spat.styles["text"].bgcolor.triplet.hex == "#282a36"


def test_styles_must_be_strings():
    pattern_str = """
    [styles]
    text = 282
    """
    with pytest.raises(DyeSyntaxError):
        Pattern.loads(pattern_str)


def test_style_theme(sthmpat):
    """a style that is only defined in the theme"""
    assert sthmpat.styles["themeonly"].bgcolor.name == "#393b47"


def test_style_pattern_overrides_theme(sthm, spat, sthmpat):
    """a color defined in both pattern and theme, make sure pattern overrides"""
    # here's the definition from the theme
    assert sthm.styles["foreground"].color.name == "#f8f8f2"
    # make sure we get the same answer whether we load the theme or not
    assert spat.styles["foreground"].color.name == "#e9e9e3"
    assert sthmpat.styles["foreground"].color.name == "#e9e9e3"


def test_style_reference_color_only_in_theme(sthmpat):
    assert sthmpat.styles["text_colorref"].color.name == "#f8f8f2"


def test_style_color_ref(sthmpat):
    """a style that references a color"""
    assert sthmpat.styles["foreground"].color.name == sthmpat.colors["foreground"]


def test_style_no_color_reference(sthmpat):
    """test a style that doesn't reference any colors, just a plain
    hexcode as the definition"""
    assert sthmpat.styles["color1"].color.name == "#ff79c6"
    assert sthmpat.styles["color1"].color.triplet.hex == "#ff79c6"


def test_styles_reference(sthmpat):
    """a style that references another style as {{styles.text_high}}"""
    assert sthmpat.styles["text_high"] == sthmpat.styles["text"]


def test_style_reference(sthmpat):
    """a style that references another style as {{style.text_medium}}"""
    assert sthmpat.styles["text_medium"] == sthmpat.styles["text"]


def test_styles_bare_reference(sthmpat):
    assert sthmpat.styles["text_low"] == sthmpat.styles["text"]


def test_styles_double1_reference(sthmpat):
    assert sthmpat.styles["text_double1"] == sthmpat.styles["text"]


def test_styles_double2_reference(sthmpat):
    assert sthmpat.styles["text_double2"] == sthmpat.styles["text"]


def test_style_unknown_color_reference(sthmpat):
    # look for a style object, but one that's empty
    assert isinstance(sthmpat.styles["color2"], rich.style.Style)
    assert not sthmpat.styles["color2"]


def test_style_unknown_style_reference(sthmpat):
    # look for a style object, but one that's empty
    assert isinstance(sthmpat.styles["color3"], rich.style.Style)
    assert not sthmpat.styles["color3"]


def test_styles_load_order(sthmpat):
    # look for a style object, but one that's empty
    assert isinstance(sthmpat.styles["notyet"], rich.style.Style)
    assert not sthmpat.styles["notyet"]


def test_style_empty(sthmpat):
    assert isinstance(sthmpat.styles["color4"], rich.style.Style)
    assert not sthmpat.styles["color4"]


def test_styles_subtable(sthmpat):
    assert isinstance(sthmpat.styles["triad_sty"], dict)
    assert sthmpat.styles["triad_sty.first"].color.name == "#aaaaaa"


def test_styles_subtable_reference1(sthmpat):
    assert sthmpat.styles["triad_sty.second"].color.name == "#cccccc"


def test_styles_subtable_reference2(sthmpat):
    assert sthmpat.styles["triad_sty.third"].bgcolor.name == "#393b47"


#
# test variable definition and usage in the [variables] table
#
def test_variable():
    pattern_str = """
        [variables]
        varname = "value"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.variables["varname"] == "value"


def test_variables_reference():
    pattern_str = """
        [variables]
        varname = "value"
        var1 = "{{var.varname}}"
        var2 = "{{vars.varname}}"
        var3 = "{{variable.varname}}"
        var4 = "{{variables.varname}}"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.variables["var1"] == "value"
    assert pattern.variables["var2"] == "value"
    assert pattern.variables["var3"] == "value"
    assert pattern.variables["var4"] == "value"


def test_undefined_variable_reference():
    pattern_str = """
        [variables]
        varname = "value"
        var1 = "{{var.notdefined}}"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.variables["var1"] == ""


def test_variables_color_reference():
    pattern_str = """
        [colors]
        bright_green = "#99e343"

        [variables]
        var1 = "{{color.bright_green}}"
        var2 = "{{colors.bright_green}}"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.variables["var1"] == "#99e343"
    assert pattern.variables["var1"] == "#99e343"


def test_variables_style_reference():
    pattern_str = """
        [styles]
        bright_green = "#99e343"

        [variables]
        var1 = "{{style.bright_green|fg_hex}}"
        var2 = "{{styles.bright_green|fg_hex}}"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.variables["var1"] == "#99e343"
    assert pattern.variables["var1"] == "#99e343"


def test_capture_variable():
    pattern_str = """
        [variables]
        capture.somevar = "printf 'hello there'"
    """
    pattern = Pattern.loads(pattern_str)
    assert pattern.variables["somevar"] == "hello there"


def test_capture_variable_error():
    pattern_str = """
        [variables]
        capture.somevar = "barf_is_not_a_shell_command"
    """
    with pytest.raises(DyeError):
        Pattern.loads(pattern_str)


def test_variable_redefine1_error():
    pattern_str = """
        [variables]
        somevar = "builtin echo hi"
        somevar = "can't do this"
    """
    with pytest.raises(tomlkit.exceptions.KeyAlreadyPresent):
        Pattern.loads(pattern_str)


def test_variable_redefine2_error():
    pattern_str = """
        [variables]
        capture.somevar = "builtin echo hi"
        somevar = "can't do this"
    """
    with pytest.raises(DyeError):
        Pattern.loads(pattern_str)


#
# test a few scope related things
#
def test_has_scope():
    pattern_str = """
        [scopes.qqq]
        agent = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    pattern = Pattern.loads(pattern_str)

    assert pattern.has_scope("qqq")
    assert not pattern.has_scope("fred")


def test_scopes():
    pattern_str = """
        [scopes.qqq]
        agent = "iterm"
        style.foreground = "blue"
        style.background = "white"

        [scopes.fff]
        agent = "environment_variables"
        unset = "listvar"
    """
    pattern = Pattern.loads(pattern_str)

    assert len(pattern.scopes) == 2
    assert isinstance(pattern.scopes["qqq"], Scope)
    assert pattern.scopes["fff"].name == "fff"


def test_scopes_empty():
    pattern_str = """
        [variables]
        hi = "there"
    """
    pattern = Pattern.loads(pattern_str)

    assert len(pattern.scopes) == 0
    assert pattern.scopes == {}


#
# test other methods
#
COLOR_DEFS = [
    ("foreground_high", DefinitionSource.THEME, "foreground"),
    ("pattern_purple", DefinitionSource.PATTERN, "#bd93f8"),
    ("triad.first", DefinitionSource.THEME, "#aaaaaa"),
    ("triad.second", DefinitionSource.PATTERN, "#dd2222"),
]


@pytest.mark.parametrize("color_name, expected_source, expected_defn", COLOR_DEFS)
def test_get_color_def_theme(sthmpat, color_name, expected_source, expected_defn):
    (source, defn) = sthmpat.get_color_def(color_name)
    assert source == expected_source
    assert defn == expected_defn


def test_get_color_def_notfound(sthmpat):
    with pytest.raises(KeyError):
        sthmpat.get_color_def("notfoundhere")


STYLE_DEFS = [
    ("themeonly", DefinitionSource.THEME, "{{color.foreground}} on #393b47"),
    ("pattern_text_low", DefinitionSource.PATTERN, "#999999 on #ffffff"),
]


@pytest.mark.parametrize("style_name, expected_source, expected_defn", STYLE_DEFS)
def test_get_style_def_theme(sthmpat, style_name, expected_source, expected_defn):
    (source, defn) = sthmpat.get_style_def(style_name)
    assert source == expected_source
    assert defn == expected_defn


def test_get_style_def_notfound(sthmpat):
    with pytest.raises(KeyError):
        sthmpat.get_style_def("notfoundhere")
