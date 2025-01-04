# TODO list for shell-themer

[ ] noctis theme ideas: https://github.com/liviuschera/noctis/pull/11
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
[x] move environment variables into their own generator instead of
    processing them in every generator
[x] add a style format for ansi codes on and off, so you can use
    the style in an 'echo' command
[ ] create a way to save the output of a shell command in a variable
[x] make a way to interpolate current environment variables, like with
    {env:HOME}
[x] make a way to capture output of a shell command into a variable
[ ] change variable interpolation and style interpolation to raise
    errors if the variable or style is not defined. because environment
    variables are defined outside of the theme file, we still interpolate
    an empty string for an undefined environment variable
[ ] make iterm generator smart enabled, ie check if iterm is the terminal emulator
    and if not, don't generate any output, but maybe generate a comment
[ ] make enabled_if and enabled generate more detailed comments
[ ] how can/should we interpolate values from a style that has bold, or both
    foreground and background definitions?


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
- recipe for changing starship config when you change a theme by changing the environment
  variable containing the starship config file

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
[x] add a command which shows all the known generators, with a short description of each
[ ] rationalize command line arguments. Some commands like list don't use -f or -t. But multiple
    commands (list, preview) use -f and -t. Currently -f and -t are not in a subparser, so you can
    supply those arguments with the list command, but that's incorrect.
[ ] create the concept of a palette, which defines a set of standard named styles. Make the
    palette saved in a file separate from the theme. The out of the box themes reference
    the standard named styles, making it possible for users to create a new palette with their
    desired colors instead of reworking an entire theme. Then we can create one standard theme
    included with shell-themer which includes all the generators. Many users can just choose
    a color palette instead of modifying or creating a theme.
[ ] see if we can download/convert/create our palettes from an online repository of color themes
[ ] add generator for GREP_COLORS https://www.gnu.org/software/grep/manual/grep.html#index-GREP_005fCOLORS-environment-variable



## Recipe ideas

- show how to enable a scope only for a certain operating system
- show how to enable a scope only on certain hosts
- show how to run a macos shortcut from a scope
-
