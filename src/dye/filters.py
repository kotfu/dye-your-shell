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
"""Filter functions for jinja"""

import rich


def jinja_filters():
    """return a dictionary of all the filters

    suitable for use by:

    env = jinja2.Environment()
    env.filters = all_filters()
    """
    filters = {}
    filters["fg_hex"] = fg_hex
    filters["fg_hex_no_hash"] = fg_hex_no_hash
    filters["fg_rgb"] = fg_rgb
    filters["bg_hex"] = bg_hex
    filters["bg_hex_no_hash"] = bg_hex_no_hash
    filters["bg_rgb"] = bg_rgb
    filters["ansi_on"] = ansi_on
    filters["ansi_off"] = ansi_off
    return filters


def fg_hex(value):
    """when applied to a style, get the hex value of the foreground color"""
    if isinstance(value, rich.style.Style):
        if value.color and not value.color.is_default:
            return value.color.get_truecolor().hex
        # empty or default styles don't have a color
        return ""
    # filter applied to something that wasn't a style, no-op
    return value


def fg_hex_no_hash(value):
    """when applied to a style, get the hex value (minus the hash mark)
    of the foreground color"""
    if isinstance(value, rich.style.Style):
        if value.color and not value.color.is_default:
            return value.color.get_truecolor().hex.replace("#", "")
        # empty or default styles don't have a color
        return ""
    # filter applied to something that wasn't a style, no-op
    return value


def fg_rgb(value):
    """when applied to a style, get a rgb function representation
    of the foreground color"""
    if isinstance(value, rich.style.Style):
        if value.color and not value.color.is_default:
            return value.color.get_truecolor().rgb
        # empty or default styles don't have a color
        return ""
    # filter applied to something that wasn't a style, no-op
    return value


def bg_hex(value):
    """when applied to a style, get the hex value of the background color"""
    if isinstance(value, rich.style.Style):
        if value.bgcolor and not value.bgcolor.is_default:
            return value.bgcolor.get_truecolor().hex
        # not all styles have a background color, if they don't
        # or if it's the default color, return an empty string
        return ""
    # filter applied to something that wasn't a style, no-op
    return value


def bg_hex_no_hash(value):
    """when applied to a style, get the hex value (minus the hash mark)
    of the foreground color"""
    if isinstance(value, rich.style.Style):
        if value.bgcolor and not value.bgcolor.is_default:
            return value.bgcolor.get_truecolor().hex.replace("#", "")
        # not all styles have a background color, if they don't
        # or if it's the default color, return an empty string
        return ""
    # filter applied to something that wasn't a style, no-op
    return value


def bg_rgb(value):
    """when applied to a style, get a rgb function representation
    of the background color"""
    if isinstance(value, rich.style.Style):
        if value.bgcolor and not value.bgcolor.is_default:
            return value.bgcolor.get_truecolor().rgb
        # not all styles have a background color, if they don't
        # or if it's the default color, return an empty string
        return ""
    # filter applied to something that wasn't a style, no-op
    return value


def ansi_on(value):
    """when applied to a style, get the ansi codes to tell the terminal
    to start printing text in that style"""
    if isinstance(value, rich.style.Style):
        splitter = "-----"
        ansistring = value.render(splitter)
        out, _ = ansistring.split(splitter)
        return out
    return value


def ansi_off(value):
    """when applied to a style, get the ansi codes to tell the terminal
    to stop printing text in that style"""
    if isinstance(value, rich.style.Style):
        splitter = "-----"
        ansistring = value.render(splitter)
        _, out = ansistring.split(splitter)
        return out
    return value
