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
