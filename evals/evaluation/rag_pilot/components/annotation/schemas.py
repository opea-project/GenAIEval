# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from llama_index.core.schema import TextNode

class SuggestionItem(BaseModel):
    node_id: Optional[str] = None
    node_page_label: Optional[str] = None
    node_context: Optional[str] = None
    confidence_score: Optional[float] = None
    best_match_score: Optional[float] = None
    best_match_context: Optional[str] = None

class GTMatchResult(BaseModel):
    context_id: int
    context_text: str
    matched_chunk: Optional[TextNode] = None
    suggestion_items: Optional[List[SuggestionItem]] = None

class QueryGTMatchResults(BaseModel):
    query_id: int
    query: str
    context_map: Dict[int, GTMatchResult] = Field(default_factory=dict)


class AnnotationRequest(BaseModel):
    query_id: int
    query: str
    context_id: int
    gt_file_name: str
    gt_text_content: str
    gt_section: Optional[str] = None
    gt_pages: Optional[List[str]] = None
    gt_metadata: Optional[Dict[str, Any]] = None

    # Matching parameters
    similarity_threshold: float = Field(default=0.8)
    enable_fuzzy: bool = Field(default=False)
    confidence_topn: int = Field(default=5)

class AnnotationResponse(BaseModel):
    success: bool
    message: str
    suggestion_items: Optional[List[SuggestionItem]] = None

