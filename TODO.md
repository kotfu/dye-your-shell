# TODO list for dye

[ ] noctis theme ideas: https://github.com/liviuschera/noctis/pull/11
[ ] figure out how to set emacs theme
[ ] make iterm generator smart enabled, ie check if iterm is the terminal emulator
    and if not, don't generate any output, but maybe generate a comment
[ ] make enabled_if and enabled generate more detailed comments
[ ] add a command like preview to validate a theme, ie did you define a 'text' style,
    do you have a description and type, etc.
[ ] should jinja environment have undefined=jinja2.StrictUndefined, ie should we generate
    errors on unknown references or keep silently replacing them with empty strings
[ ] make 'dye themes' show some basic info about each theme, type, description, etc.
[ ] switch to uv
[ ] add a command like apply that validates a pattern
    - description exists
    - prevent_themes is boolean if present
    - requires_theme refers to a file that exists
[ ] make a 'dye patterns' command that lists out the patterns, need it for theme-activate() bash func
[ ] write unit tests for pattern.py for stitching together a theme and a pattern
[ ] switch from colors.red and styles.text and variables.myvar to the singular
    version of each. The pattern file just reads so much nicer.
[ ] make styles do a lookup like they used to, ie "style.prompt = 'my_style'"
    it's so much more readable than '{{styles.my_style}}. Do the same thing for
    colors
[ ] see if we can download/convert/create our palettes from an online repository of color themes
[ ] add generator for GREP_COLORS https://www.gnu.org/software/grep/manual/grep.html#index-GREP_005fCOLORS-environment-variable
[ ] figure out how to add support for eza theme files
[ ] make a filecopy generator, that just copies a file from one location to another, you can use
    this to support many tools which look at their own config file for color information, you
    create multiple config files, and this generator copies the one that matches your theme
    to the "real config" file. Tools like eza themes, starship, etc. could use this
[ ] make a recipe that shows how to use the shell_command generator to copy files, like to
    support multiple starship configs
[ ] create a page that shows various ways to create table entries (i.e. inline method style.directory, or separate table method)
[ ] create a 'template-jinja' generator which can process a template file or inline string and then write
    write it out to the filesystem somewhere. Use this to get your theme info into other config
    files like starship.toml. So you would create starship.toml.template and 'shell-themer' would
    process it and insert your theme colors/variables/etc and output a starship.toml for you
[ ] if you use ansi color numbers or names (instead of hex codes) in a style, it won't interpolate properly
    because the interpolator assumes that the color has a .triplet. See rich.color.get_truecolor() which
    we can use to fix this

## documentation and website
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



## Recipe ideas

- show how to enable a scope only for a certain operating system
- show how to enable a scope only on certain hosts
- show how to run a macos shortcut from a scope
-
