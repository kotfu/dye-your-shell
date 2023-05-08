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
"""generator base class"""

import abc
import re


class Generator(abc.ABC):
    """Abstract Base Class for all generators

    Subclass and implement generate()

    Creates a registry of all subclasses in cls.generators

    The string to use in your theme configuration file is the underscored
    class name, ie:

    EnvironmentVariables -> environment_variables
    LsColors -> ls_colors
    """
    generators = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # make a registry of subclasses as they are defined
        cls.generators[cls._name_of(cls.__name__)] = cls

    def __init__(self, scope, scopedef):
        super().__init__()
        self.scope = scope
        self.scopedef = scopedef

    @classmethod
    def _name_of(cls, name: str) -> str:
        """Make an underscored, lowercase form of the given class name."""
        name = re.sub(r"Generator$", '', name)
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', name)
        name = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', name)
        name = name.replace("-", "_")
        return name.lower()

    @abc.abstractmethod
    def generate(self) -> str:
        """generate a string of text, with newlines, which can be sourced by bash

        returns an empty string if there is nothing to generate
        """
        return ''
