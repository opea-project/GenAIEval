# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from dataclasses_json import dataclass_json

from . import metrics


@dataclass_json
@dataclass
class RetrievedDoc:
    doc_id: Optional[str] = None
    text: str = ""


@dataclass_json
@dataclass
class RAGResult:
    query_id: str
    query: str
    gt_answer: str
    response: str
    retrieved_contexts: List[RetrievedDoc] = None  # Retrieved documents
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass_json
@dataclass
class RAGResults:
    results: List[RAGResult] = field(default_factory=list)
    metrics: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            metrics.overall_metrics: {},
            metrics.retriever_metrics: {},
            metrics.generator_metrics: {},
        }
    )

    def __repr__(self) -> str:
        metrics = "  " + "\n  ".join(json.dumps(self.metrics, indent=2).split("\n"))
        return f"RAGResults(\n  {len(self.results):,} RAG results,\n" f"  Metrics:\n{metrics}\n)"

    def update(self, rag_result: List[RAGResult]):
        self.results.append(rag_result)
        self.metrics = {metrics.overall_metrics: {}, metrics.retriever_metrics: {}, metrics.generator_metrics: {}}
