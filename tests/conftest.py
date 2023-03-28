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

from shell_themer import Themer


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
