# TODO list for shell-themer

- documentation and website
  - show how to set BAT_THEME
- figure out how to set emacs theme
- make a mini-language so that environment_render() can put styles
  in various color formats into an environment variable
- add a condition to every scope, ie
  [scope.iterm]
  if = "some shell command here"

  if the command returns 0 then we process the scope
  if the command returns not 0 the we skip processing the scope

- document how to load a theme
    - eval $(shell-themer) is bad, try the code from `$ starship init bash` instead

- document a "magic" styles named "background", "foreground", and "text"
  - these will be used by the preview command to show the style properly
  - text should be foreground on background

## shell-themer subcommands

[x] themes = -f and -t are ignored, shows a list of all available themes from $THEME_DIR
[x] preview = show the theme name, version, and file, and all active styles from the specified theme or from $THEME_DIR
[x] {activate|process|render|brew|make|generate} = process the theme and spew out all the environment variables
  - don't like activate because it doesn't really activate the theme
  - don't like process because we use processors for something else
  - generate seems the best so far, then we have generator = "fzf"
- init = generate the code for the theme-activate, theme-reload, and theme-choose (using fzf)
- help = show help
