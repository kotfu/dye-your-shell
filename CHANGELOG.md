# Changelog

All notable changes to [shell-themer](https://github.com/kotfu/shell-themer)
are documented in this file.

This project uses [Semantic Versioning](http://semver.org/spec/v2.0.0.html) and the
format of this file follows recommendations from
[Keep a Changelog](http://keepachangelog.com/en/1.0.0/).


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


