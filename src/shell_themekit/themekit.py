#!/usr/bin/env python
#
# given a scope, like "ls.directory", get the color associated with that scope
#
# options:
#   --format -- what format do you want the color in {hex, rgb, escape codes)
#   --theme -- can be specified here, if not, uses $THEME_DIR environment
#              variable
#
#   --default -- if the scope isn't present in the theme
#     use this instead, or do we build this into the theme?
#

# approach
# - compile the theme file into a bunch of rich.style objects, with
#   a method get_style() that gets the style from the theme or parses
#   it from the input
# - make a custom python function for each type of rendered output
#    - ie fzf render type would create an options string for fzf
#      including --color, --border, --pointer, --prompt, --marker etc
#    - ls render type would create a LS_COLORS string
#    - envhex creates environment variables with hex codes in them for
#      each variable in the scope
# - create a scope that set an env variable, like to set BAT_THEME
#    - the theme file just contains the name of the bat theme to use when this
#      shell theme is selected
# - create a scope that knows how to set an emacs theme by name
#    - the theme file contains the name of the emacs theme



# parse the "styles" section into a dict[str, Style]
# we don't need the theme stack from the method below, we just
# need to check the dict for the style, or parse it
# 
# use
    # def get_style(
    #     self, name: Union[str, Style], *, default: Optional[Union[Style, str]] = None
    # ) -> Style:
    #     """Get a Style instance by its theme name or parse a definition.

    #     Args:
    #         name (str): The name of a style or a style definition.

    #     Returns:
    #         Style: A Style object.

    #     Raises:
    #         MissingStyle: If no style could be parsed from name.

    #     """
    #     if isinstance(name, Style):
    #         return name

    #     try:
    #         style = self._theme_stack.get(name)
    #         if style is None:
    #             style = Style.parse(name)
    #         return style.copy() if style.link else style
    #     except errors.StyleSyntaxError as error:
    #         if default is not None:
    #             return self.get_style(default)
    #         raise errors.MissingStyle(
    #             f"Failed to get style {name!r}; {error}"
    #         ) from None
            
# to get

import tomllib
import os
import pathlib
import sys

import rich.color
import rich.console

class ThemeKit():
    """parse and translate a theme file for various command line programs
    """
    
    def load(self):
        """load a theme from a file"""
        pass
        