#
#

import pytest
import rich.style
import rich.errors

from shell_themekit import Theme


@pytest.fixture
def thm_base():
    thm = Theme(prog="shell-themekit")
    return thm


@pytest.fixture
def thm(thm_base):
    # a theme object loaded up with a robust configuration
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

[domain.fzf]
type = "fzf"

# attributes specific to fzf
varname = "FZF_DEFAULT_OPTS"

# command line options
opt.--prompt = ">"
opt.--border = "single"
opt.--pointer = "•"
opt.--info = "hidden"
opt.--no-sort = true

# styles
style.text = "foreground"
style.label = "green"
style.border = "orange"
style.selected = "current_line"
style.prompt = "green"
style.indicator = "cyan"
style.match = "pink"
style.localstyle = "green on black"

[domain.noattribs]

style.text = "foreground"
"""
    thm_base.loads(tomlstr)
    return thm_base


def test_loads_empty(thm_base):
    thm_base.loads("")
    assert isinstance(thm_base.definition, dict)
    assert thm_base.definition == {}
    assert isinstance(thm_base.styles, dict)
    assert thm_base.styles == {}


def test_parse_styles(thm):
    assert isinstance(thm.styles, dict)
    assert isinstance(thm.styles["cyan"], rich.style.Style)
    assert thm.styles["cyan"].color.name == "#8be9fd"
    assert thm.styles["yellow"].color.name == "#f1fa8c"


def test_domain_styles(thm):
    domain = "fzf"
    styles = thm.domain_styles(domain)
    assert isinstance(styles, dict)
    assert len(styles) == 8
    assert "indicator" in styles.keys()
    assert isinstance(styles["localstyle"], rich.style.Style)
    style = styles["selected"]
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


def test_domain_elements_unknown(thm):
    domain = "unknown"
    styles = thm.domain_styles(domain)
    assert isinstance(styles, dict)
    assert styles == {}


def test_domain_attributes(thm):
    attribs = thm.domain_attributes("fzf")
    assert isinstance(attribs, dict)
    assert attribs["type"] == "fzf"
    assert len(attribs) == 3
    with pytest.raises(KeyError):
        _ = attribs["style"]
    assert thm.definition["domain"]["fzf"]["style"]["text"] == "foreground"


def test_domain_attributes_none(thm):
    attribs = thm.domain_attributes("noattribs")
    assert isinstance(attribs, dict)
    assert attribs == {}


def test_get_style_plain(thm):
    style = thm.get_style("#aaff00")
    assert isinstance(style, rich.style.Style)
    assert style.color.name == "#aaff00"


def test_get_style_complex(thm):
    style = thm.get_style("bold white on red")
    assert isinstance(style, rich.style.Style)
    assert style.bold == True
    assert style.color.name == "white"
    assert style.bgcolor.name == "red"


def test_get_style_invalid(thm):
    with pytest.raises(rich.errors.StyleSyntaxError):
        style = thm.get_style("not a valid style")


def test_get_style_lookup(thm):
    style = thm.get_style("current_line")
    assert style.color.name == "#f8f8f2"
    assert style.bgcolor.name == "#44475a"


ATTRIBS_TO_FZF = [
    ("bold", "regular:bold"),
    ("underline", "regular:underline"),
    ("reverse", "regular:reverse"),
    ("dim", "regular:dim"),
    ("italic", "regular:italic"),
    ("strike", "regular:strikethrough"),
    ("bold underline", "regular:bold:underline"),
    ("underline italic", "regular:underline:italic"),
    ("italic underline", "regular:underline:italic"),
]


@pytest.mark.parametrize("styledef, fzf", ATTRIBS_TO_FZF)
def test_fzf_attribs_from_style(thm, styledef, fzf):
    style = rich.style.Style.parse(styledef)
    assert fzf == thm._fzf_attribs_from_style(style)


STYLE_TO_FZF = [
    # text, current_line, and preview styles have special processing
    # for foreground and background colors
    ("text", "", ""),
    ("text", "default", "fg:-1:regular"),
    ("text", "default on default", "fg:-1:regular,bg:-1"),
    ("text", "bold default on default underline", "fg:-1:regular:bold:underline,bg:-1"),
    ("text", "white on bright_red", "fg:7:regular,bg:9"),
    ("text", "bright_white", "fg:15:regular"),
    ("text", "bright_yellow on color(4)", "fg:11:regular,bg:4"),
    ("text", "green4", "fg:28:regular"),
    ("current_line", "navy_blue dim on grey82", "fg+:17:regular:dim,bg+:252"),
    # other styles do not
    ("preview", "#af00ff on bright_white", "preview-fg:#af00ff:regular,preview-bg:15"),
    ("border", "magenta", "border:5:regular"),
    ("query", "#2932dc", "query:#2932dc:regular"),
]


@pytest.mark.parametrize("name, styledef, fzf", STYLE_TO_FZF)
def test_fzf_from_style(thm, name, styledef, fzf):
    style = rich.style.Style.parse(styledef)
    assert fzf == thm._fzf_from_style(name, style)
