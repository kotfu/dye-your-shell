# dye-your-shell

activate color output in shell commands using themes and patterns

There are many modern *nix and *bsd command line tools which can output
using a full 16.7 million color palette. For example:

* [fzf](https://github.com/junegunn/fzf)
* [dust](https://github.com/bootandy/dust)
* [bat](https://github.com/sharkdp/bat)
* [gum](https://github.com/charmbracelet/gum)
* [eza](https://eza.rocks/)

Even the GNU Project's venerable `ls` can show various types of files in
different colors.

Unfortunately, these tools all use slightly different color configuration mechanisms.
With enough fiddling, you can get your shell init scripts to make all these tools
use a similar color scheme, but if you want to change it, you've got a lot of work
ahead.

`dye-your-shell` installs a command line program named `dye` to do its work.

`dye` reads a configuration file containing a set of colors, and instructions on how to
apply those colors to as many command line tools as can support it. This configuration
file is called a pattern. Each command line tool (ie bat, fzf, eza) has it's own set of
instructions in the pattern which are powered by an agent, which is included in `dye`.
This agent knows how to easily apply the colors to that command line tool, for example
by setting an environment variable, or executing certain shell commands, or copying
a template to a config file.

Instead of tweaking your collection of bash scripts to create or change all these
colors, you now just tell `dye` to apply your pattern.
```
export DYE_PATTERN_FILE=~/.dye/dracula.toml
source <(dye apply)
```


## Pattern Files

Here's an example of a pattern file:
```
#
# sample definition for a dracula theme

version = "1.0.0"
name = "dracula"

[styles]
# these are from https://draculatheme.com/contribute
background =  "#282a36"
foreground =  "#f8f8f2"

# styles for text and the highlighted line
# these are the only things fzf supports background colors for
text = "#f8f8f2 on default"
current_line =  "#f8f8f2 on #44475a"

# other colors from the dracula palette
comment =  "#6272a4"
cyan =  "#8be9fd"
green =  "#50fa7b"
orange =  "#ffb86c"
pink =  "#ff79c6"
purple =  "#bd93f9"
red =  "#ff5555"
yellow =  "#f1fa8c"

[scope.iterm]
agent = "iterm"
style.foreground = "foreground"
style.background = "background"

[scope.ls_colors]
agent = "environment_variables"
export.LS_COLORS = "$(vivid generate dracula)"

[scope.bat]
agent = "environment_variables"
export.BAT_THEME = "Dracula"

[scope.fzf]
agent = "fzf"
environment_variable = "FZF_DEFAULT_OPTS"
colorbase = "dark"

# command line options
opt.--pointer = "•"
opt.--prompt = "> "
opt.--bind = "ctrl-k:kill-line,ctrl-j:ignore,ctrl-u:unix-line-discard"

# these styles are special because they set both foreground and background
style.text = "text"
style.current_line = "current_line"

# no special parsing for these styles, just use the fzf color name
# highlighted substrings
style.hl = "pink"
# highlighted substrings current line
style."hl+" = "pink"
style.label = "green"
style.border = "orange"
style.prompt = "green"
style.pointer = "cyan"
style.query = "pink"
```

## Installation

You'll need python version 3.9 or higher. Install with [pipx](https://pipx.pypa.io/stable/):
```
$ pipx install dye-your-shell
```

You need a *nix-ish bash shell environment. Probably works in Windows Subsystem
for Linux, but isn't tested there.
