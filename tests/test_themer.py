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
import rich.errors

from shell_themer import Themer


EXIT_SUCCESS = 0
EXIT_ERROR = 1


@pytest.fixture
def thm_base():
    thm = Themer(prog="shell-themer")
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

[domain.ls]
# set some environment variables
environment.unset = ["SOMEVAR", "ANOTHERVAR"]
environment.export.LS_COLORS = "ace ventura"

[domain.unset]
# unset a single variable
environment.unset = "NOLISTVAR"

[domain.fzf]
processor = "fzf"

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


[domain.bash-control-r]
processor = "fzf"
# select the environment variable
environment_variable = "FZF_CTRL_R_OPTS"

# command line options
opt.--border = "rounded"
opt.--border-label = "command history"
opt.--border-label-pos = "3"

# styles
style.gutter = "default"


[domain.noprocessor]
# without a processor defined, this will not render anything
style.text = "foreground"

[domain.unknownprocessor]
processor = "unknown"

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
    assert attribs["processor"] == "fzf"
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
    assert style.bold is True
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


#
# test general rendering
#
def test_render_single(thm, capsys):
    exit_code = thm.render(["fzf"])
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert out
    assert not err
    assert out.count("\n") == 1


def test_render_unknown(thm, capsys):
    exit_code = thm.render(["unknowndomain"])
    out, err = capsys.readouterr()
    assert exit_code == EXIT_ERROR
    assert not out
    assert err


def test_render_all(thm, capsys):
    exit_code = thm.render()
    assert exit_code == EXIT_SUCCESS
    out, err = capsys.readouterr()
    assert out
    assert not err
    assert out.count("\n") == 6


def test_processor_unknown(thm, capsys):
    exit_code = thm.render("unknownprocessor")
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not out
    assert not err


#
# test environment rendering
#
def test_render_environment_unset_list(thm, capsys):
    exit_code = thm.render(["ls"])
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert out
    assert not err
    assert "unset SOMEVAR" in out
    assert "unset ANOTHERVAR" in out
    assert 'export LS_COLORS="ace ventura"' in out


def test_render_environment_unset_string(thm, capsys):
    # we are testing a string domain instead of a list here on purpose
    exit_code = thm.render("unset")
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert out
    assert not err
    assert "unset NOLISTVAR" in out


#
# test the fzf processor
#
def test_fzf_opts(thm_base, capsys):
    tomlstr = """
[domain.fzf]
processor = "fzf"
environment_variable = "QQQ"
opt."+i" = true
opt.--border = "rounded"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not err
    assert out == """export QQQ=" +i --border='rounded'"\n"""


def test_fzf_no_opts(thm_base, capsys):
    tomlstr = """
[domain.fzf]
processor = "fzf"
environment_variable = "QQQ"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not err
    assert out == """export QQQ=""\n"""


def test_fzf_no_varname(thm_base, capsys):
    tomlstr = """
[domain.fzf]
processor = "fzf"
opt."+i" = true
opt.--border = "rounded"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_ERROR
    assert not out
    assert "fzf processor requires 'environment_variable'" in err


#
# test the ls_colors processor
#
# we only reallly have to test that the style name maps to the right code in ls_colors
# ie directory -> di, or setuid -> su. The ansi codes are created by rich.style
# so we don't really need to test much of that
STYLE_TO_LSCOLORS = [
    ("text", "", ""),
    ("text", "default", "no=0"),
    ("file", "default", "fi=0"),
    ("directory", "#8be9fd", "di=38;2;139;233;253"),
    ("symlink", "green4 bold", "ln=1;38;5;28"),
    ("multi_hard_link", "blue on white", "mh=34;47"),
    ("pipe", "#f8f8f2 on #44475a underline", "pi=4;38;2;248;248;242;48;2;68;71;90"),
    ("socket", "bright_white", "so=97"),
    ("door", "bright_white", "do=97"),
    ("block_device", "default", "bd=0"),
    ("character_device", "black", "cd=30"),
    ("broken_symlink", "bright_blue", "or=94"),
    ("missing_symlink_target", "bright_blue", "mi=94"),
    ("setuid", "bright_blue", "su=94"),
    ("setgid", "bright_red", "sg=91"),
    ("sticky", "blue_violet", "st=38;5;57"),
    ("other_writable", "blue_violet italic", "ow=3;38;5;57"),
    ("sticky_other_writable", "deep_pink2 on #ffffaf", "tw=38;5;197;48;2;255;255;175"),
    ("executable_file", "cornflower_blue on grey82", "ex=38;5;69;48;5;252"),
    ("file_with_capability", "red on black", "ca=31;40"),
]


@pytest.mark.parametrize("name, styledef, lsc", STYLE_TO_LSCOLORS)
def test_ls_colors_from_style(thm_base, name, styledef, lsc):
    style = rich.style.Style.parse(styledef)
    assert lsc == thm_base._ls_colors_from_style(name, style)


def test_ls_colors_no_styles(thm_base, capsys):
    tomlstr = """
[domain.lsc]
processor = "ls_colors"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not err
    assert out == 'export LS_COLORS=""\n'


def test_ls_colors_environment_variable(thm_base, capsys):
    tomlstr = """
[domain.lsc]
processor = "ls_colors"
environment_variable = "OTHER_LS_COLOR"
style.file = "default"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not err
    assert out == 'export OTHER_LS_COLOR="fi=0"\n'


def test_ls_colors_clear_builtin(thm_base, capsys):
    tomlstr = """
[domain.lsc]
processor = "ls_colors"
clear_builtin = true
style.directory = "bright_blue"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not err
    assert (
        out
        == 'export LS_COLORS="no=0:fi=0:di=94:ln=0:mh=0:pi=0:so=0:do=0:bd=0:cd=0:or=0:mi=0:su=0:sg=0:st=0:ow=0:tw=0:ex=0:ca=0"\n'
    )


def test_ls_colors_clear_builtin_not_boolean(thm_base, capsys):
    tomlstr = """
[domain.lsc]
processor = "ls_colors"
clear_builtin = "error"
style.directory = "bright_blue"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_ERROR
    assert not out
    assert "'clear_builtin' to be boolean" in err


#
# test the iterm processor
#
def test_iterm(thm_base, capsys):
    tomlstr = """
[domain.iterm]
processor = "iterm"
style.foreground = "#ffeebb"
style.background = "#221122"
    """
    thm_base.loads(tomlstr)
    exit_code = thm_base.render()
    out, err = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 2
    assert lines[0] == r'builtin echo -n "\033]1337;SetColors=fg=ffeebb\007"'
    assert lines[1] == r'builtin echo -n "\033]1337;SetColors=bg=221122\007"'
