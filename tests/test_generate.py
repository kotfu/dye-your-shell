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


#
# test high level generation functions
#
def test_generate_single_scope(thm_cmdline, capsys):
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
    exit_code = thm_cmdline("generate -s fzf", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert out
    assert not err
    assert out.count("\n") == 1


def test_generate_unknown_scope(thm_cmdline, capsys):
    tomlstr = """
        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"

        [scope.iterm]
        generator = "iterm"
        style.foreground = "foreground"
        style.background = "background"

        [scope.ls]
        # set some environment variables
        environment.unset = ["SOMEVAR", "ANOTHERVAR"]
        environment.export.LS_COLORS = "ace ventura"
    """
    exit_code = thm_cmdline("generate -s unknownscope", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert err


def test_generate_no_scopes(thm_cmdline, capsys):
    tomlstr = """
        [styles]
        background =  "#282a36"
        foreground =  "#f8f8f2"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not out
    assert not err


#
# test rendering of elements common to all scopes
#
def test_generate_enabled(thm_cmdline, capsys):
    tomlstr = """
        [scope.nolistvar]
        enabled = false
        generator = "environment_variables"
        environment.unset = "NOLISTVAR"

        [scope.somevar]
        enabled = true
        generator = "environment_variables"
        environment.unset = "SOMEVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert "unset SOMEVAR" in out
    assert not "unset NOLISTVAR" in out


def test_generate_enabled_false_enabled_if_ignored(thm_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        enabled = false
        enabled_if = "[[ 1 == 1 ]]"
        generator = "environment_variables"
        environment.unset = "NOLISTVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert not out


def test_generate_enabled_true_enabed_if_ignored(thm_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        enabled = true
        enabled_if = "[[ 0 == 1 ]]"
        generator = "environment_variables"
        environment.unset = "NOLISTVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert "unset NOLISTVAR" in out


def test_generate_enabled_invalid_value(thm_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        enabled = "notaboolean"
        generator = "environment_variables"
        environment.unset = "NOLISTVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert "to be true or false" in err


ENABLED_IFS = [
    ("", True),
    ("echo", True),
    ("[[ 1 == 1 ]]", True),
    ("[[ 1 == 0 ]]", False),
    ("{var:echocmd} hi", True),
    ("{variable:falsetest}", False),
]


@pytest.mark.parametrize("cmd, enabled", ENABLED_IFS)
def test_generate_enabled_if(cmd, enabled, thm_cmdline, capsys):
    tomlstr = f"""
        [variables]
        echocmd = "/bin/echo"
        falsetest = "[[ 1 == 0]]"

        [scope.unset]
        enabled_if = "{cmd}"
        generator = "environment_variables"
        environment.unset = "ENVVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    if enabled:
        assert "unset ENVVAR" in out
    else:
        assert not out


def test_generate_comments(thm_cmdline, capsys):
    tomlstr = """
        [scope.nolistvar]
        enabled = false
        generator = "environment_variables"
        environment.unset = "NOLISTVAR"

        [scope.somevar]
        enabled = true
        generator = "environment_variables"
        environment.unset = "SOMEVAR"
    """
    exit_code = thm_cmdline("generate --comment", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert "# [scope.nolistvar]" in out
    assert "# [scope.somevar]" in out
    assert "unset SOMEVAR" in out
    assert not "unset NOLISTVAR" in out


def test_unknown_generator(thm_cmdline, capsys):
    tomlstr = """
        [scope.myprog]
        generator = "mrfusion"
        environment.unset = "SOMEVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    _, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert "unknown generator" in err
    assert "mrfusion" in err


def test_no_generator(thm_cmdline, capsys):
    tomlstr = """
        [scope.myscope]
        enabled = false
    """
    exit_code = thm_cmdline("generate", tomlstr)
    _, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert "does not have a generator defined" in err
    assert "myscope" in err


#
# test the environment_variables generator
#
ENV_INTERPOLATIONS = [
    ("{style:dark_orange}", "#ff6c1c"),
    ("{style:dark_orange:hex}", "#ff6c1c"),
    ("{style:dark_orange:hexnohash}", "ff6c1c"),
    # for an unknown format or style, don't do any replacement
    ("{style:current_line}", "{style:current_line}"),
    ("{style:dark_orange:unknown}", "{style:dark_orange:unknown}"),
    # we have to have the style keyword, or it all just gets passed through
    ("{dark_orange}", "{dark_orange}"),
    ("{variable:green}", "{variable:green}"),
    # escaped opening bracket, becasue this is toml, if you want a backslash
    # you have to you \\ because toml strings can contain escape sequences
    (r"\\{style:bright_blue}", "{style:bright_blue}"),
    # if you don't have matched brackets, or are missing the
    # literal 'style:' keyword, don't expect the backslash
    # to be removed. again here we have two backslashes in the first
    # argument so that it will survive toml string escaping
    (r"\\{ some other  things}", r"\{ some other  things}"),
    (r"\\{escaped unmatched bracket", r"\{escaped unmatched bracket"),
    # try a mixed variable and style interpolation
    ("{style:dark_orange} {var:someopts}", "#ff6c1c --option=fred -v"),
]


@pytest.mark.parametrize("phrase, interpolated", ENV_INTERPOLATIONS)
def test_generate_environment_interpolation(thm_cmdline, capsys, phrase, interpolated):
    tomlstr = f"""
        [variables]
        someopts = "--option=fred -v"

        [styles]
        dark_orange = "#ff6c1c"

        [scope.gum]
        generator = "environment_variables"
        environment.export.GUM_OPTS = " --cursor-foreground={phrase}"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert out == f'export GUM_OPTS=" --cursor-foreground={interpolated}"\n'


def test_generate_environment_unset_list(thm_cmdline, capsys):
    tomlstr = """
        [scope.ls]
        generator = "environment_variables"
        # set some environment variables
        environment.unset = ["SOMEVAR", "ANOTHERVAR"]
        environment.export.LS_COLORS = "ace ventura"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert "unset SOMEVAR" in out
    assert "unset ANOTHERVAR" in out
    assert 'export LS_COLORS="ace ventura"' in out


def test_generate_environment_unset_string(thm_cmdline, capsys):
    tomlstr = """
        [scope.unset]
        generator = "environment_variables"
        environment.unset = "NOLISTVAR"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert "unset NOLISTVAR" in out


#
# test the fzf generator
#
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


def test_fzf_opts(thm_cmdline, capsys):
    tomlstr = """
        [variables]
        bstyle = "rounded"

        [scope.fzf]
        generator = "fzf"
        environment_variable = "QQQ"
        opt."+i" = true
        opt.--border = "{var:bstyle}"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == """export QQQ=" +i --border='rounded'"\n"""


def test_fzf_no_opts(thm_cmdline, capsys):
    tomlstr = """
        [variables]
        varname = "ZZ"
        [scope.fzf]
        generator = "fzf"
        environment_variable = "Q{var:varname}QQ"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == """export QZZQQ=""\n"""


def test_fzf_no_varname(thm_cmdline, capsys):
    tomlstr = """
        [scope.fzf]
        generator = "fzf"
        opt."+i" = true
        opt.--border = "rounded"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert "fzf generator requires 'environment_variable'" in err


#
# test the ls_colors generator
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
    ("so", "bright_white", "so=97"),
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


@pytest.mark.parametrize("name, styledef, expected", STYLE_TO_LSCOLORS)
def test_ls_colors_from_style(thm, name, styledef, expected):
    style = rich.style.Style.parse(styledef)
    code, render = thm._ls_colors_from_style(name, style, thm.LS_COLORS_MAP, "scope")
    assert render == expected
    assert code == expected[0:2]


def test_ls_colors_no_styles(thm_cmdline, capsys):
    tomlstr = """
        [scope.lsc]
        generator = "ls_colors"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == 'export LS_COLORS=""\n'


def test_ls_colors_unknown_style(thm_cmdline, capsys):
    tomlstr = """
        [scope.lsc]
        generator = "ls_colors"
        style.bundleid = "default"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert "unknown style" in err
    assert "lsc" in err


def test_ls_colors_environment_variable(thm_cmdline, capsys):
    tomlstr = """
        [scope.lsc]
        generator = "ls_colors"
        environment_variable = "OTHER_LS_COLOR"
        style.file = "default"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == 'export OTHER_LS_COLOR="fi=0"\n'


def test_ls_colors_clear_builtin(thm_cmdline, capsys):
    tomlstr = """
        [scope.lsc]
        generator = "ls_colors"
        clear_builtin = true
        style.directory = "bright_blue"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    expected = (
        'export LS_COLORS="di=94:no=0:fi=0:ln=0:'
        "mh=0:pi=0:so=0:do=0:bd=0:cd=0:or=0:mi=0:"
        'su=0:sg=0:st=0:ow=0:tw=0:ex=0:ca=0"\n'
    )
    assert out == expected


def test_ls_colors_clear_builtin_not_boolean(thm_cmdline, capsys):
    tomlstr = """
        [scope.lsc]
        generator = "ls_colors"
        clear_builtin = "error"
        style.directory = "bright_blue"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert "'clear_builtin' to be true or false" in err


#
# test the exa_colors generator
#
# we only reallly have to test that the style name maps to the right code in ls_colors
# ie directory -> di, or setuid -> su. The ansi codes are created by rich.style
# so we don't really need to test much of that
STYLE_TO_EXACOLORS = [
    ("text", "", ""),
    ("text", "default", "no=0"),
    ("file", "default", "fi=0"),
    ("directory", "#8be9fd", "di=38;2;139;233;253"),
    ("symlink", "green4 bold", "ln=1;38;5;28"),
    ("multi_hard_link", "blue on white", "mh=34;47"),
    ("pi", "#f8f8f2 on #44475a underline", "pi=4;38;2;248;248;242;48;2;68;71;90"),
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
    ("sn", "#7060eb", "sn=38;2;112;96;235"),
]


@pytest.mark.parametrize("name, styledef, expected", STYLE_TO_EXACOLORS)
def test_exa_colors_from_style(thm, name, styledef, expected):
    style = rich.style.Style.parse(styledef)
    code, render = thm._ls_colors_from_style(name, style, thm.EXA_COLORS_MAP, "scope")
    assert render == expected
    assert code == expected[0:2]


def test_exa_colors_no_styles(thm_cmdline, capsys):
    tomlstr = """
        [scope.exac]
        generator = "exa_colors"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == 'export EXA_COLORS=""\n'


def test_exa_colors_unknown_style(thm_cmdline, capsys):
    tomlstr = """
        [scope.exac]
        generator = "exa_colors"
        style.bundleid = "default"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert "unknown style" in err
    assert "exac" in err


def test_exa_colors_environment_variable(thm_cmdline, capsys):
    tomlstr = """
        [scope.exac]
        generator = "exa_colors"
        environment_variable = "OTHER_EXA_COLOR"
        style.file = "default"
        style.size_number = "#7060eb"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == 'export OTHER_EXA_COLOR="fi=0:sn=38;2;112;96;235"\n'


def test_exa_colors_clear_builtin(thm_cmdline, capsys):
    tomlstr = """
        [scope.exac]
        generator = "exa_colors"
        clear_builtin = true
        style.directory = "bright_blue"
        style.uu = "bright_red"
        style.punctuation = "#555555"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    expected = 'export EXA_COLORS="reset:di=94:uu=91:xx=38;2;85;85;85"\n'
    assert out == expected


def test_exa_colors_clear_builtin_not_boolean(thm_cmdline, capsys):
    tomlstr = """
        [scope.exac]
        generator = "exa_colors"
        clear_builtin = "error"
        style.directory = "bright_blue"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_ERROR
    assert not out
    assert "'clear_builtin' to be true or false" in err


#
# test the iterm generator
#
def test_iterm(thm_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        generator = "iterm"
        style.foreground = "#ffeebb"
        style.background = "#221122"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 2
    assert lines[0] == r'builtin echo -e "\e]1337;SetColors=fg=ffeebb\a"'
    assert lines[1] == r'builtin echo -e "\e]1337;SetColors=bg=221122\a"'


def test_iterm_bgonly(thm_cmdline, capsys):
    tomlstr = """
        [scope.iterm]
        generator = "iterm"
        style.background = "#b2cacd"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    lines = out.splitlines()
    assert len(lines) == 1
    assert lines[0] == r'builtin echo -e "\e]1337;SetColors=bg=b2cacd\a"'


#
# test the shellcommand generator
#
def test_shell(thm_cmdline, capsys):
    tomlstr = """
        [variables]
        greeting = "hello there"

        [styles]
        purple = "#A020F0"

        [scope.shortcut]
        generator = "shell"
        command.first = "echo {var:greeting}"
        command.next = "echo general kenobi"
        command.last = "echo {style:purple}"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert out == "echo hello there\necho general kenobi\necho #a020f0\n"


def test_shell_enabled_if(thm_cmdline, capsys):
    # we have separate tests for enabled_if, but since it's super useful with the
    # shell generator, i'm including another test here
    tomlstr = """
        [scope.shortcut]
        generator = "shell"
        enabled_if = "[[ 1 == 0 ]]"
        command.first = "shortcuts run 'My Shortcut Name'"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert not out


def test_shell_multiline(thm_cmdline, capsys):
    tomlstr = """
        [scope.multiline]
        generator = "shell"
        command.long = '''
echo hello there
echo general kenobi
if [[ 1 == 1 ]]; then
  echo "yes sir"
fi
'''
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    # yes we have two line breaks at the end of what we expect
    # because there are single line commands, we have to output
    # a newline after the command
    # but on multiline commands that might give an extra newline
    # at the end of the day, that makes zero difference in
    # functionality, but it matters for testing, hence this note
    expected = """echo hello there
echo general kenobi
if [[ 1 == 1 ]]; then
  echo "yes sir"
fi

"""
    assert out == expected


def test_shell_no_commands(thm_cmdline, capsys):
    tomlstr = """
        [scope.shortcut]
        generator = "shell"
    """
    exit_code = thm_cmdline("generate", tomlstr)
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    assert not out
