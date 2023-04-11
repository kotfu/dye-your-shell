#
# -*- coding: utf-8 -*-
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
# pylint: disable=protected-access, missing-function-docstring, redefined-outer-name
# pylint: disable=missing-module-docstring, unused-variable

from unittest import mock

from shell_themer import Themer


#
# test the list command
#
def test_list(thm_cmdline, capsys, mocker, tmp_path):
    # gotta patch the theme dir, we don't want it throwing errors if not set
    dirmock = mocker.patch(
        "shell_themer.Themer.theme_dir", create=True, new_callable=mock.PropertyMock
    )
    dirmock.return_value = tmp_path
    # write some empty toml files into the directory
    bases = ["one", "two", "three"]
    for base in bases:
        path = tmp_path / f"{base}.toml"
        with open(path, "w", encoding="utf8") as fvar:
            fvar.write(f"# a toml file for theme {base}")
    # now go run the command, which should list the themes
    exit_code = thm_cmdline("list")
    out, err = capsys.readouterr()
    assert exit_code == Themer.EXIT_SUCCESS
    assert not err
    for base in bases:
        assert base in out
