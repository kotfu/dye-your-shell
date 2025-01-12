# Changelog

All notable changes to [dye-your-shell](https://github.com/kotfu/dye-your-shell)
are documented in this file.

This project uses [Semantic Versioning](http://semver.org/spec/v2.0.0.html)
and the format of this file follows recommendations from
[Keep a Changelog](http://keepachangelog.com/en/1.0.0/).


## [0.9.0] - 2025/01/11

### Changed

- `ls_colors` agent renamed to `gnu_ls`

### Removed

- removed `exa_colors` agent because exa is unmaintained. Use
  [eza](https://eza.rocks/) instead with the `eza` agent


### Fixed

- last release didn't include all dependencies and was therefore broken. This
  has been fixed.


## [0.8.0] - 2025-01-09

### Changed

- renamed distribution from shell_themer to dye-your-shell
- rename package from shell_themer to dye (command line tool is now dye)
- themes have been split into themes (colors and styles), and patterns
  (scopes and agents)
- this release is still pretty rough, if you care if it works well,
  maybe wait for the next one


## [0.7.0] - 2025-01-07

### Added

- `eza` agent now allows defining styles for arbitrary file globs

### Changed

- generators are now called agents
- `eza_colors` agent renamed to `eza`
- `eza` agent uses the same style names as the theme files used by eza,
  instead of the custom ones
- `fzf` agent no longer requires `environment_variable` directive, if
  not specified it defaults to `FZF_DEFAULT_OPTS`
- `fzf` agent now has foreground/background combined style support for
  `selected-line`


## [0.6.0] - 2025-01-04

### Changed

- minor changes and improvements to release process, no code changes


## [0.5.0] - 2025-01-04

### Added

- New style formats `bg` and `bghex` to output the background color
- New style format `fg` and `fghex` to output the foreground color

### Changed

- `hex` and `hexnohash` are no longer a valid style interpolation formats, use
  `fghex`, `bghex`, `fghexnohash` or `bghexnohash` instead.


## [0.4.0] - 2025-01-03

### Added

- New command "generators" which lists all known generators
- New generator for [eza](https://github.com/eza-community/eza) colors
- `ansi_on` and `ansi_off` style formats
- Add iterm generator directives for changing cursor color and shape
- Add iterm generator directive to change the iterm profile
- Add iterm generator directive to change the tab or window title background color
- Add new {env:HOME} interpolation for shell environment variables
- Add capture variables which set their value from the output of shell commands

### Changed

- Simplify directives in environment_variables generator


## [0.3.0] - 2023-05-07

### Added

- generator for [exa](https://the.exa.website/) colors


## [0.2.0] - 2023-04-19

### Added

- variable and style interpolation
- shell generator to run any shell command when activating a theme
- add `--color` command line option and `SHELL_THEMER_COLORS` environment
  variable to change colors of help output
- support for NO_COLOR, see [https://no-color.org/](https://no-color.org)


## [0.1.0] - 2023-04-01

### Added

- generators for fzf, LS_COLORS, and iterm


