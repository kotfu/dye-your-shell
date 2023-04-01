# shell-themer

There are many modern *nix and *bsd command line tools which can output
using a full 16.7 million color palette. For example:

* [fzf](https://github.com/junegunn/fzf)
* [dust](https://github.com/bootandy/dust)
* [bat](https://github.com/sharkdp/bat)
* [gum](https://github.com/charmbracelet/gum)

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

## Installation

You'll need python version 3.7 or higher. Install with pip:
```
pip install shell_themer
```

You need a *nix-ish bash shell environment. Probably works in Windows Subsystem
for Linux, but isn't tested there.
