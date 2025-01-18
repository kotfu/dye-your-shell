#
# Copyright (c) 2023 Jared Crapo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
"""utility functions"""

from importlib import metadata

import benedict
import rich

from .exceptions import DyeSyntaxError


def version_string():
    """return a version string suitable for display to a user"""
    try:
        # this is the distribution name, not the package name
        ver = metadata.version("dye-your-shell")
    except metadata.PackageNotFoundError:  # pragma: nocover
        ver = "unknown"
    return ver


def merge_and_process_colors(base_colors, merging_colors, jinja_env):
    """merge together two benedicts of colors (one or both can be empty) and
    process references and templates in all the values.

    Args:
        base_colors (benedict): _description_
        merging_colors (benedict): _description_
        jinja_env (jinja2.environments): _description_

    base_colors will be modified to include all of the items in merging_colors.

    items in merging_colors will overwrite items already in base_colors.

    Used by Theme and Pattern objects

    This assumes that base_colors (if present) has already been processed. If
    you just need to process one dict, call this like

        processed_dict = benedict()
        merge_and_process_colors(processed_dict, unprocessed_dict)

    that will result in processed_dict having all the keys of unprocessed_dict
    but all the values will have been processed
    """
    # iterate over all the keys in raw_colors, processing and inserting
    # the values into self.colors
    keylist = merging_colors.keypaths(sort=False)
    for key in keylist:
        value = merging_colors[key]
        if isinstance(value, str):
            if value in base_colors:
                # bare lookup so that foreground_low = "foreground" works
                base_colors[key] = base_colors[value]
            else:
                template = jinja_env.from_string(value)
                base_colors[key] = template.render(
                    # this lets us do {{colors.foreground}} or {{color.foreground}}
                    colors=base_colors,
                    color=base_colors,
                )
        elif isinstance(value, dict):
            # So we rely on and test for the fact that both the subtable name
            # (with the dict value) and each of the subtable keys show up in
            # keylist. Those other keys will be picked up in a different iteration
            # of the loop. But they shouldn't be a syntax error.
            pass
        else:
            raise DyeSyntaxError(f"color {key} must be defined as a string")


def merge_and_process_styles(base_styles, merging_styles, jinja_env, colors=None):
    """Merge together two benedicts of colors (one or both can be empty) and
    process references and templates in all the values.

    Args:
        base_styles (benedict): _description_
        merging_styles (benedict): _description_
        jinja_env (jinja2.environments): _description_
        colors (benedicty): optional benedict of processed colors

    base_styles will be modified to include all of the items in merging_styles.

    items in merging_styles will overwrite items already in base_styles.

    Used by Theme and Pattern objects

    This assumes that base_styles (if present) has already been processed. If
    you just need to process one dict, call this like

        processed_dict = benedict()
        merge_and_process_styles(processed_dict, unprocessed_dict)

    that will result in processed_dict having all the keys of unprocessed_dict
    but all the values will have been processed
    """
    if not colors:
        colors = benedict.benedict()

    keylist = merging_styles.keypaths(sort=False)
    for key in keylist:
        value = merging_styles[key]
        if isinstance(value, str):
            if value in base_styles:
                # bare lookup so that foreground_low = "foreground" works
                base_styles[key] = base_styles[value]
            else:
                template = jinja_env.from_string(value)
                rendered = template.render(
                    # allow {{style.foreground}} or {{styles.foreground}}
                    # or {{color.background}} or {{colors.background}}
                    color=colors,
                    colors=colors,
                    style=base_styles,
                    styles=base_styles,
                )
                base_styles[key] = rich.style.Style.parse(rendered)
        elif isinstance(value, dict):
            # So we rely on and test for the fact that both the subtable name
            # (with the dict value) and each of the subtable keys show up in
            # keylist. Those other keys will be picked up in a different iteration
            # of the loop. But they shouldn't be a syntax error.
            pass
        else:
            raise DyeSyntaxError(f"theme {key} must be defined as a string")
