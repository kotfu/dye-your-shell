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


def version_string():
    """return a version string suitable for display to a user"""
    try:
        # this is the distribution name, not the package name
        ver = metadata.version("dye-your-shell")
    except metadata.PackageNotFoundError:  # pragma: nocover
        ver = "unknown"
    return ver


def deep_map(data, process_func, *args, **kwargs):
    """
    Recursively iterate through a nested data structure and apply process_func to each
    value. Works with nested dictionaries, lists, and individual values.

    Mutates all values in place.

    Args:
        data: Input dictionary, list, or value process_func: Function to apply to each
        value *args: Additional positional arguments to pass to process_func **kwargs:
        Additional keyword arguments to pass to process_func

    Returns:
        Same structure as input, with process_func applied to all values
    """
    if isinstance(data, dict):
        # build a new dictionary with a recursive call on each value
        return {
            key: deep_map(value, process_func, *args, **kwargs)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        # build a new list with a recursive call on each item
        return [deep_map(item, process_func, *args, **kwargs) for item in data]
    else:
        # it's just an end node, call the function which will process the values
        return process_func(data, *args, **kwargs)
