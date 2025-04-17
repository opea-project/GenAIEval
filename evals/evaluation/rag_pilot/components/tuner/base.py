# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import Enum, auto
from typing import Callable, List, Optional, Tuple, Union

from pydantic import BaseModel, validator


class ContentType(Enum):
    ALL_CONTEXTS = auto()
    CONTEXT = auto()
    RESPONSE = auto()


class OptionItem(BaseModel):
    idx: int
    content: str

    def __str__(self):
        return f"{self.idx}: {self.content}"


class UserInput(BaseModel):
    hint: str
    options: Optional[List[OptionItem]] = None

    @validator("options", pre=True)
    def auto_generate_ids(cls, v):
        if v is None:
            return v
        if all(isinstance(item, str) for item in v):
            return [{"idx": idx, "content": item} for idx, item in enumerate(v, start=1)]
        return v

    def __str__(self):
        options_str = ""
        if self.options:
            options_str = "\n" + "\n".join(str(option) for option in self.options)
        return f"{self.hint}{options_str}"


class Question(UserInput):
    status: Optional[str] = None

    def __str__(self):
        status_str = f"{self.status}\n" if self.status else ""
        options_str = ""
        if self.options:
            options_str = "\n" + "\n".join(str(option) for option in self.options)
        return f"{status_str}{self.hint}{options_str}"


class SuggestionType(Enum):
    CHOOSE = auto()
    ITERATE = auto()
    SET = auto()
    STEPWISE_GROUPED = auto()
    STEPWISE = auto()
    GRID_SEARCH = auto() 


class Suggestion(UserInput):
    suggestion_type: SuggestionType


class Feedback(BaseModel):
    feedback: bool | int


class DirectionType(Enum):
    INCREASE = auto()
    DECREASE = auto()


class Target(BaseModel):
    node_type: str
    module_type: Optional[str] = None
    attribute: str
    orig_val: Optional[Union[int, float, str]] = None
    new_vals: List[Union[int, float, str]] = None
    suggestion: Suggestion = None
