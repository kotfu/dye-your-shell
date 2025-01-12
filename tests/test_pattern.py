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

from dye import DyeError, DyeSyntaxError, Pattern, Theme

SAMPLE_THEME = """
[colors]
foreground = "#f8f8f2"
foreground_high = "foreground"
foreground_medium = "foreground"
foreground_low = "foreground"

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
    pattern.process()
    return pattern


@pytest.fixture
def sthmpat():
    """the sample pattern with the sample theme merged into it"""
    theme = Theme.loads(SAMPLE_THEME)
    pattern = Pattern.loads(SAMPLE_PATTERN)
    pattern.process(theme)
    return pattern


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
    # Pattern.load() uses the same code as Pattern.loads(), so we don't
    # have to retest everything. If loads() works and load() can
    # open and read the file, load() will work too
    assert len(pat.definition) == 9


def test_loads(spat):
    assert isinstance(spat.definition, dict)
    assert len(spat.definition) == 9


def test_loads_empty():
    pat = Pattern.loads("")
    assert pat.definition == {}
    # assert pat.colors == {}
    # assert theme.styles == {}


def test_loads_none():
    pat = Pattern.loads(None)
    assert pat.definition == {}
    # assert pat.colors == {}
    # assert theme.styles == {}


def test_loads_colors(spat):
    assert isinstance(spat.colors, dict)
    assert isinstance(spat.colors["pattern_purple"], str)
    assert spat.colors["pattern_purple"] == "#bd93f8"
    assert len(spat.colors) == 12


def test_loads_styles(spat):
    assert isinstance(spat.styles, dict)
    assert isinstance(spat.styles["pattern_text"], rich.style.Style)
    assert isinstance(spat.styles["pattern_text_high"], rich.style.Style)
    assert len(spat.styles) == 17


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
    assert pat.description is None


def test_prevent_themes():
    pattern_str = """prevent_themes = true"""
    pat = Pattern.loads(pattern_str)
    assert pat.prevent_themes is True


def test_prevent_themes_not_present():
    pattern_str = """description = 'hi'"""
    pat = Pattern.loads(pattern_str)
    assert pat.prevent_themes is False


def test_prevent_themes_not_boolean():
    pattern_str = "prevent_themes = 'nope'"
    pat = Pattern.loads(pattern_str)
    with pytest.raises(DyeSyntaxError):
        _ = pat.prevent_themes


def test_requires_theme():
    pattern_str = """requires_theme = '/path/to/theme'"""
    pat = Pattern.loads(pattern_str)
    assert pat.requires_theme == "/path/to/theme"


def test_requires_theme_not_present():
    pattern_str = """description = 'hi'"""
    pat = Pattern.loads(pattern_str)
    assert pat.requires_theme is None


def test_has_scope():
    pattern_str = """
        [scopes.qqq]
        agent = "iterm"
        style.foreground = "blue"
        style.background = "white"
    """
    pattern = Pattern.loads(pattern_str)
    pattern.process()

    assert pattern.has_scope("qqq")
    assert not pattern.has_scope("fred")


#
# test processing of colors
#
def test_color_pattern(sthmpat):
    """a color that is only defined in the pattern"""
    assert sthmpat.colors["background"] == "#282a36"


def test_color_theme(sthmpat):
    """a color that is only defined in the theme"""
    assert sthmpat.colors["foreground_high"] == "#f8f8f2"


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


#
# test processing of styles
#
def test_style_pattern(spat):
    """defined only in the pattern, referencing colors
    only in the pattern"""
    assert spat.styles["text"].color.name == "#e9e9e3"
    assert spat.styles["text"].color.triplet.hex == "#e9e9e3"
    assert spat.styles["text"].bgcolor.name == "#282a36"
    assert spat.styles["text"].bgcolor.triplet.hex == "#282a36"


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


#
# test variable definition and usage in the [variables] table
#
def test_variable():
    pattern_str = """
        [variables]
        varname = "value"
    """
    pattern = Pattern.loads(pattern_str)
    pattern.process()
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
    pattern.process()
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
    pattern.process()
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
    pattern.process()
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
    pattern.process()
    assert pattern.variables["var1"] == "#99e343"
    assert pattern.variables["var1"] == "#99e343"


def test_capture_variable():
    pattern_str = """
        [variables]
        capture.somevar = "printf 'hello there'"
    """
    pattern = Pattern.loads(pattern_str)
    pattern.process()
    assert pattern.variables["somevar"] == "hello there"


def test_capture_variable_error():
    pattern_str = """
        [variables]
        capture.somevar = "barf_is_not_a_shell_command"
    """
    pattern = Pattern.loads(pattern_str)
    with pytest.raises(DyeError):
        pattern.process()


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
    pattern = Pattern.loads(pattern_str)
    with pytest.raises(DyeError):
        pattern.process()


#
# TODO test variable usage in scopes, ie Scope object or Pattern._process_scopes()
# TODO test scope processing


# # TODO this should test the init in GeneratorBase which sets scope_styles
# # def test_styles_from(thm):
# #     tomlstr = """
# #         [styles]
# #         background =  "#282a36"
# #         foreground =  "#f8f8f2"
# #         current_line =  "#f8f8f2 on #44475a"
# #         comment =  "#6272a4"
# #         cyan =  "#8be9fd"
# #         green =  "#50fa7b"
# #         orange =  "#ffb86c"
# #         pink =  "#ff79c6"
# #         purple =  "#bd93f9"
# #         red =  "#ff5555"
# #         yellow =  "#f1fa8c"

# #         [scope.iterm]
# #         generator = "iterm"
# #         style.foreground = "foreground"
# #         style.background = "background"

# #         [scope.fzf]
# #         generator = "fzf"

# #         # attributes specific to fzf
# #         environment_variable = "FZF_DEFAULT_OPTS"

# #         # command line options
# #         opt.--prompt = ">"
# #         opt.--border = "single"
# #         opt.--pointer = "•"
# #         opt.--info = "hidden"
# #         opt.--no-sort = true
# #         opt."+i" = true

# #         # styles
# #         style.text = "foreground"
# #         style.label = "green"
# #         style.border = "orange"
# #         style.selected = "current_line"
# #         style.prompt = "green"
# #         style.indicator = "cyan"
# #         style.match = "pink"
# #         style.localstyle = "green on black"
# #     """
# #     thm.loads(tomlstr)
# #     scopedef = thm.scopedef_for("fzf")
# #     styles = thm.styles_from(scopedef)
# #     assert isinstance(styles, dict)
# #     assert len(styles) == 8
# #     assert "indicator" in styles.keys()
# #     assert isinstance(styles["localstyle"], rich.style.Style)
# #     style = styles["selected"]
# #     assert style.color.name == "#f8f8f2"
# #     assert style.bgcolor.name == "#44475a"


# # TODO I don't think we need to test this, as long as we test the
# # init() method of GeneratorBase
# # def test_styles_from_unknown(thm):
# #     tomlstr = """
# #         [scope.iterm]
# #         generator = "iterm"
# #         style.foreground = "foreground"
# #         style.background = "background"
# #     """
# #     thm.loads(tomlstr)
# #     scopedef = thm.scopedef_for("unknown")
# #     styles = thm.styles_from(scopedef)
# #     assert isinstance(styles, dict)
# #     assert styles == {}
