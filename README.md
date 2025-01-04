# shell-themer

There are many modern *nix and *bsd command line tools which can output
using a full 16.7 million color palette. For example:

* [fzf](https://github.com/junegunn/fzf)
* [dust](https://github.com/bootandy/dust)
* [bat](https://github.com/sharkdp/bat)
* [gum](https://github.com/charmbracelet/gum)
* [exa](https://the.exa.website/)

Even the venerable `ls` can show various types of files in different colors.

Unfortunately, these tools all use slightly different color configuration mechanisms.
With enough fiddling, you can get your shell init scripts to make all these tools
use a similar color scheme, but if you want to change it, you've got a lot of work
ahead.

`shell-themer` uses a single theme configuration file to standardize and unify
a set of color configurations, and generates the shell code to implement those
changes.

All that hand tweaking in your shell init files can now be replaced with:
```
export THEME_FILE=~/themes/dracula.toml
source <(shell-themer generate)
```

This changes all your environment variables and other settings for the many
shell tools you use to reflect the colors in the theme you have specified.

## Theme Files

Here's an example of a theme file:
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
generator = "iterm"
style.foreground = "foreground"
style.background = "background"

[scope.ls_colors]
generator = "environment_variables"
environment.export.LS_COLORS = "$(vivid generate dracula)"

[scope.bat]
generator = "environment_variables"
environment.export.BAT_THEME="Dracula"

[scope.fzf]
generator = "fzf"
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
$ pipx install shell_themer
```

You need a *nix-ish bash shell environment. Probably works in Windows Subsystem
for Linux, but isn't tested there.
