# TODO list for shell-themer

[ ] figure out how to set emacs theme
[x] make a mini-language so that environment_render() can put styles
    in various color formats into an environment variable
[x] add a condition to every scope, ie
  [scope.iterm]
  disable = true
  // exit code 0 is true, and means to disable it
  // any other exit code means to not disable it
  disable_if = "some shell command here"
  // if you have to negate the exit code, try
  // isiterm2 && [[ $? == 0 ]]
[x] add option to generate to insert comments into the output
[x] allow creation of variables with values, which can be interpolated
    into other sections
[ ] move environment variables into their own generator instead of
    processing them in every generator

- documentation and website
  - show how to set BAT_THEME
- document how to load a theme
    - eval $(shell-themer) is bad, try the code from `$ starship init bash` instead
- document a "magic" styles named "background", "foreground", and "text"
  - these will be used by the preview command to show the style properly
  - text should be foreground on background
- document environment interpolations
- document variable interpolations
- document enabled and enabled_if - enabled_if shell commands should not cause side effects because
  they can get executed on a "dry run" of generation
- document shell generator, including multiline commands and usage with enable_if

## shell-themer subcommands

[x] themes = -f and -t are ignored, shows a list of all available themes from $THEME_DIR
[x] preview = show the theme name, version, and file, and all active styles from the specified theme or from $THEME_DIR
[x] {activate|process|render|brew|make|generate} = process the theme and spew out all the environment variables
  - don't like activate because it doesn't really activate the theme
  - don't like process because we use processors for something else
  - generate seems the best so far, then we have generator = "fzf"
- init = generate the code for the theme-activate (using fzf if not specified), theme-reload
[x] honor NO_COLOR env variable
[x] add --no-color option
[x] add --colors= option
[x] add SHELL_THEMER_COLORS env variable


## Recipe ideas

- show how to enable a scope only for a certain operating system
- show how to enable a scope only on certain hosts
- show how to run a macos shortcut from a scope
-
