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

from .exceptions import DyeSyntaxError


def version_string():
    """return a version string suitable for display to a user"""
    try:
        # this is the distribution name, not the package name
        ver = metadata.version("dye-your-shell")
    except metadata.PackageNotFoundError:  # pragma: nocover
        ver = "unknown"
    return ver


def benedict_keylist(d):
    """return a list of keys from a benedict

    benedict.keypaths() sorts the keypaths, and our use case requires
    order to be preserved. I stole these two lines of code from
    benedict.keypaths(), they are the ones right before the .sort()

    I've submitted a PR to python-benedict to add a `sort` parameter to
    keylists. If/when that PR is merged, this utility function could go
    away.
    """
    kls = benedict.core.keylists(d)
    return [".".join([f"{key}" for key in kl]) for kl in kls]


def colors_merge_and_process(base_colors, merging_colors, jinja_env):
    """merge together two benedicts of colors (one or both can be empty) and
    process references and templates in all the values.

    base_colors will be modified to include all of the items in merging_colors.

    items in merging_colors will overwrite items already in base_colors.

    Used by Theme and Pattern objects

    This assumes that base_colors (if present) has already been processed. If
    you just need to process one dict, call this like

        processed_dict = benedict()
        colors_merge_and_process(processed_dict, unprocessed_dict)

    that will result in processed_dict having all the keys of unprocessed_dict
    but all the values will have been processed
    """
    # iterate over all the keys in raw_colors, processing and inserting
    # the values into self.colors
    keylist = benedict_keylist(merging_colors)
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
