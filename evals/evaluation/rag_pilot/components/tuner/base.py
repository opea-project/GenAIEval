# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Optional, Callable, Union, List, Tuple

from pydantic import BaseModel


class RagResult(BaseModel):
    query: str
    contexts: Optional[List[str]] = None
    ground_truth: Optional[str] = None
    response: str


class ContentType(str, Enum):
    ALL_CONTEXTS = "all_contexts"
    CONTEXT = "context"
    RESPONSE = "response"


class QuestionType(str, Enum):
    RATING5 = "1-5"
    RATING3 = "1-3"
    BOOL = "y/n"
    SCORE = "Input a number"
    MINUS_ONE_ZERO_ONE = "-1, 0, 1"


class Question(BaseModel):
    question: str
    question_type: QuestionType
    content_type: ContentType


class Feedback(BaseModel):
    type: QuestionType
    feedback: bool | int


class SuggestionType(str, Enum):
    SET = "set"
    OFFSET = "offset"
    CHOOSE = "choose"


class DirectionType(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"


class SuggestionValue(BaseModel):
    suggestion_type: SuggestionType
    step: Optional[int] = None
    direction: Optional[DirectionType] = None
    choices: Optional[List] = None
    val: Optional[Union[int, float, str]] = None


class Suggestion(BaseModel):
    attribute: str
    svalue: SuggestionValue
    origval: Optional[Union[int, float, str]] = None
    is_accepted: bool = False

    def reset(self):
        self.is_accepted = False
        self.origval = None
        self.svalue.val = None
        self.svalue.direction = None
        self.svalue.choices = None
