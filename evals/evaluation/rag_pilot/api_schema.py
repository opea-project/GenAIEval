# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import uuid
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class RunningStatus(str, Enum):
    INACTIVE = "inactive"
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RAGStage(str, Enum):
    RETRIEVAL = "retrieval"
    POSTPROCESSING = "postprocessing"
    GENERATION = "generation"


class TunerAttribute(BaseModel):
    type: str
    params: Dict


class TunerModule(BaseModel):
    type: str
    params: Optional[Dict] = Field(default_factory=dict)
    attributes: Optional[List[TunerAttribute]] = Field(default_factory=list)


class Tuner(BaseModel):
    type: str
    params: Optional[Dict] = Field(default_factory=dict)
    modules: Optional[List[TunerModule]] = Field(default_factory=list)


class TunerRequest(BaseModel):
    stage: RAGStage
    tuners: List[Tuner] = Field(default_factory=list)


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


class GroundTruthContextSuggestion(BaseModel):
    node_id: Optional[str] = None
    node_page_label: Optional[str] = None
    node_context: Optional[str] = None
    confidence_score: Optional[float] = None
    best_match_score: Optional[float] = None
    best_match_context: Optional[str] = None


class GroundTruthContext(BaseModel):
    filename: str
    text: str
    context_id: int
    pages: Optional[List[str]] = None
    section: Optional[str] = None
    suggestions: Optional[List[GroundTruthContextSuggestion]] = None


class GroundTruth(BaseModel):
    query_id: int
    query: str
    contexts: List[GroundTruthContext]
    answer: Optional[str] = None


class MatchSettings(BaseModel):
    hit_threshold: Optional[float] = None
    enable_fuzzy: Optional[bool] = None
    confidence_topn: Optional[int] = None


class AnnotationOutput(BaseModel):
    suggested_query_ids: list[int]


class PilotSettings(BaseModel):
    # {ECRAG_SERVICE_HOST_IP}:{ECRAG_SERVICE_PORT}
    target_endpoint: Optional[str] = None
    target_type: Optional[str] = "ecrag"
