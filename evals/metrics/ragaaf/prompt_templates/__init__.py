# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .opening_prompt import OpeningPrompt

from .correctness import Correctness
from .factualness import Factualness
from .relevance import Relevance
from .readability import Readability

__all__ = ["opening_prompt", "correctness", "factualness", "relevance", "readability"]

NAME2METRIC = {}


def snake2camel(s):
    return "".join(x.capitalize() or "_" for x in s.split("_"))


for name in __all__:
    NAME2METRIC[name] = eval(snake2camel(name))
