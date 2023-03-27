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
