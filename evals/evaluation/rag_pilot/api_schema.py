# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class RunningStatus(str, Enum):
    INACTIVE = "inactive"
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RAGStage(str, Enum):
    RETRIEVAL = "retrieval"
    POSTPROCESSING = "postprocessing"
    GENERATION = "generation"


class TunerOut(BaseModel):
    stage: str
    name: str
    targets: str
    status: str


class TunerUpdateOut(BaseModel):
    tuner_name: Optional[str] = None
    base_pipeline_id: Optional[uuid.UUID] = None
    pipeline_id: uuid.UUID
    targets: Dict[str, Union[str, int]]


class ContextItem(BaseModel):
    context_idx: Optional[int] = None
    file_name: Optional[str] = None
    text: Optional[str] = ""
    metadata: Optional[Dict[str, Union[int, float]]] = {}


class ResultOut(BaseModel):
    query_id: int
    metadata: Optional[Dict[str, Union[int, float]]] = {}
    query: Optional[str] = None
    ground_truth: Optional[str] = None
    response: Optional[str] = None
    gt_contexts: Optional[List[ContextItem]] = None
    retrieval_contexts: Optional[List[ContextItem]] = None
    postprocessing_contexts: Optional[List[ContextItem]] = None


class ResultsOut(BaseModel):
    metadata: Optional[Dict[str, Union[int, float]]] = {}
    results: Optional[List[ResultOut]] = None


class GroundTruthContext(BaseModel):
    filename: str
    text: str


class GroundTruth(BaseModel):
    query_id: int
    query: str
    contexts: List[GroundTruthContext]
    answer: Optional[str] = None
