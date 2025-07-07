# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, List, Optional

from comps import opea_microservices, register_microservice
from pydantic import BaseModel

from .doc import RAGResults
from .metrics import *
from .metrics_parser import DeepevalMetricsParser, EvaluatorType, RagasMetricsParser

default_llm_name = "Qwen/Qwen2-7B-Instruct"


class EvaluatorCreateIn(BaseModel):

    llm_name: Optional[str] = default_llm_name
    evaluator_type: Optional[str] = EvaluatorType.RAGAS
    metrics: Optional[str] = "all_metrics"


class MetricsIn(BaseModel):

    metrics: str


class Evaluator:
    def __init__(self):
        self.metrics_parser = None


@register_microservice(
    name="opea_service@ec_rag", endpoint="/v1/settings/evaluator", host="0.0.0.0", port=16020, methods=["POST"]
)
async def create_metrics(request: EvaluatorCreateIn):
    match request.evaluator_type:
        case EvaluatorType.RAGAS:
            metrics_parser = RagasMetricsParser(request.llm_name)
        case EvaluatorType.DEEPEVAL:
            metrics_parser = DeepevalMetricsParser(request.llm_name)
        case _:
            pass
    if metrics_parser is not None:
        metrics_parser.create_metrics(request.metrics)
        evaluator.metrics_parser = metrics_parser
        return f"Metrics {request.metrics} on {request.evaluator_type} are created"
    else:
        return f"Fail to create evaluator {request.evaluator_type} with metrics {request.metrics}"


@register_microservice(
    name="opea_service@ec_rag", endpoint="/v1/settings/metrics", host="0.0.0.0", port=16020, methods=["POST"]
)
async def update_metrics(request: MetricsIn):
    if evaluator.metrics_parser is not None:
        evaluator.metrics_parser.create_metrics(request.metrics)
        return f"Metrics {request.metrics} is updated"
    else:
        return "Metrics parser is not initiated"


@register_microservice(
    name="opea_service@ec_rag", endpoint="/v1/data/ragresults", host="0.0.0.0", port=16020, methods=["POST"]
)
async def evaluate(request: RAGResults):
    if evaluator.metrics_parser is not None:
        evaluator.metrics_parser.evaluate(request)
        return repr(request)
    else:
        return "Metrics parser is not initiated"


if __name__ == "__main__":
    evaluator = Evaluator()
    opea_microservices["opea_service@ec_rag"].start()
