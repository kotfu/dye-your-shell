# TODO list for shell-themer

- documentation and website
  - show how to set BAT_THEME
- make an iterm2 processor
- figure out how to set emacs theme
- make a processor for ls to build LS_COLORS
- make a mini-language so that environment_render() can put styles
  in various color formats into an environment variable
- add a condition to every domain, ie
  [domain.iterm]
  if = "some shell command here"

  if the command returns 0 then we process the domain
  if the command returns not 0 the we skip processing the domain

- add a way for shell-themer to display the names and colors of all styles in the
  [styles] section

- document how to load a theme
    - eval $(shell-themer) is bad, try the code from `$ starship init bash` instead


## shell-themer subcommands

-f = option for most subcommands that specifies the theme file, else use $THEME_FILE
-t = option exclusive of -f for a theme name from $THEME_DIR

- themes = -f and -t are ignored, shows a list of all available themes from $THEME_DIR
- preview = show the theme name, version, and file, and all active styles from the specified theme or from $THEME_DIR
- {activate|process|render} = process the theme and spew out all the environment variables
  - don't like activate because it doesn't really activate the theme
- init = generate the code for the theme-activate, theme-reload, and theme-choose (using fzf)
- help = show help
