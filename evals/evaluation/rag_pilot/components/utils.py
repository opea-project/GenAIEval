# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


from collections import defaultdict
from typing import List, TextIO, Union

import pandas as pd
import yaml
from api_schema import GroundTruth
from components.pilot.base import ContextGT, ContextType, GTType
from components.pilot.result import RAGResult, RAGResults


def load_rag_results_from_csv(file_obj: Union[str, TextIO]):
    try:
        rag_results_raw = pd.read_csv(file_obj)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    required_columns = {"query_id", "query", "gt_context", "file_name"}
    if not required_columns.issubset(rag_results_raw.columns):
        raise ValueError(
            f"Missing required columns. Required: {required_columns}, Found: {set(rag_results_raw.columns)}"
        )

    rag_results_dict = defaultdict(lambda: {"gt_contexts": []})

    try:
        for _, rag_result in rag_results_raw.iterrows():
            query_id = rag_result.get("query_id")
            if pd.isna(query_id):
                continue

            if "query" not in rag_results_dict[query_id]:
                rag_results_dict[query_id].update(
                    {
                        "query": rag_result.get("query", ""),
                        "ground_truth": (
                            rag_result.get("ground_truth", "") if "ground_truth" in rag_results_raw.columns else ""
                        ),
                    }
                )

            gt_context = rag_result.get("gt_context", "")
            file_name = rag_result.get("file_name", "")
            file_name = "" if pd.isna(file_name) else str(file_name)

            if gt_context:
                rag_results_dict[query_id]["gt_contexts"].append(
                    ContextGT(gt_type=GTType.TRADITIONAL, text=gt_context, file_name=file_name)
                )

        rag_results = RAGResults()
        for query_id, data in rag_results_dict.items():
            result = RAGResult(
                query_id=query_id,
                query=data["query"],
                gt_contexts=data["gt_contexts"] if data["gt_contexts"] else None,
                ground_truth=data.get("ground_truth", ""),
            )
            result.init_context_idx(ContextType.GT)
            rag_results.add_result(result)

        return rag_results

    except Exception as e:
        raise ValueError(f"Error processing RAG results from CSV: {e}")


def load_rag_results_from_gt(gts: List[GroundTruth]):
    try:
        rag_results = RAGResults()
        for gt in gts:
            result = RAGResult(
                query_id=gt.query_id,
                query=gt.query,
                gt_contexts=[],
                ground_truth=gt.answer,
            )
            for ctx in gt.contexts:
                result.gt_contexts.append(ContextGT(gt_type=GTType.TRADITIONAL, text=ctx.text, file_name=ctx.filename))
            result.init_context_idx(ContextType.GT)
            rag_results.add_result(result)

        return rag_results

    except Exception as e:
        raise ValueError(f"Error processing RAG results from GroundTruth: {e}")


def load_rag_results_from_gt_match_results(gt_match_results: List):
    try:
        rag_results = RAGResults()
        for gt_match_result in gt_match_results:
            gt_contexts = []
            for context_id, context_match_res in gt_match_result.context_map.items():
                chunk = context_match_res.matched_chunk if context_match_res.matched_chunk else None
                if not chunk:
                    continue
                gt_context_item = ContextGT(
                    gt_type=GTType.ANNOTATION,
                    node_id=chunk.node_id,
                    node_text=chunk.text,
                    text=context_match_res.context_text,
                    file_name=chunk.metadata.get("file_name", "unknown"),
                    page_label=chunk.metadata.get("page_label", ""),
                )
                gt_contexts.append(gt_context_item)

            result = RAGResult(
                query_id=gt_match_result.query_id,
                query=gt_match_result.query,
                gt_contexts=gt_contexts,
                ground_truth="",  # Can be set later if available
            )
            result.init_context_idx(ContextType.GT)
            rag_results.add_result(result)
        return rag_results

    except Exception as e:
        raise ValueError(f"Error processing RAG results from GTMatchResult: {e}")


def read_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_content = file.read()
    return yaml.safe_load(yaml_content)
