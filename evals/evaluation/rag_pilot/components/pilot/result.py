# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import copy
import csv
import hashlib
import json
import re
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, model_serializer, Field
import numpy as np
import uuid

from components.pilot.base import ContextItem, ContextType, ContextGT, GTType, fuzzy_contains

# Import matcher for advanced text matching
try:
    from components.annotation.matcher import default_matcher
except ImportError:
    # Fallback in case matcher is not available
    default_matcher = None


class Metrics(str, Enum):
    RETRIEVAL_RECALL = "retrieval_recall_rate"
    POSTPROCESSING_RECALL = "postprocessing_recall_rate"
    ANSWER_RELEVANCY = "answer_relevancy"


class RAGResult(BaseModel):
    metadata: Optional[Dict[str, Union[float, int, list]]] = {}
    query_id: Optional[int] = None
    query: str
    ground_truth: Optional[str] = None
    response: Optional[str] = None

    gt_contexts: Optional[List[ContextGT]] = None
    retrieval_contexts: Optional[List[ContextItem]] = None
    postprocessing_contexts: Optional[List[ContextItem]] = None

    finished: bool = False

    def __init__(self, **data):
        super().__init__(**data)

    def __post_init__(self):
        for context_type in ContextType:
            self.init_context_idx(context_type)

    def copy(self):
        return copy.deepcopy(self)

    def update_metrics(self, metrics: Dict[str, Union[float, int]]):
        if not metrics:
            return
        if self.metadata is None:
            self.metadata = {}
        for key, value in metrics.items():
            if isinstance(value, (float, int)):
                self.metadata[key] = value

    def init_context_idx(self, context_type):
        context_list_name = f"{context_type.value}_contexts"
        context_list = getattr(self, context_list_name, None)
        if context_list is not None:
            for idx, context in enumerate(context_list):
                context.context_idx = idx

    def add_context(self, context_type: ContextType, context: ContextItem):
        context_list_name = f"{context_type.value}_contexts"
        context_list = getattr(self, context_list_name, None)
        if context_list is None:
            context_list = []
            setattr(self, context_list_name, context_list)
        context.context_idx = len(context_list)
        context_list.append(context)

    def update_metadata_hits(self, threshold=1, enable_fuzzy=False,confidence_topn=5):
        if self.gt_contexts:
            for context_type in [ContextType.RETRIEVAL, ContextType.POSTPROCESSING]:
                context_list_name = f"{context_type.value}_contexts"
                context_list = getattr(self, context_list_name, None)
                if context_list is None:
                    continue
                for context in context_list:
                    self.context_matches_gt(self.gt_contexts, context, context_type, threshold,enable_fuzzy,confidence_topn)

            for context_type in [ContextType.RETRIEVAL, ContextType.POSTPROCESSING]:
                count = 0
                for gt_context in self.gt_contexts:
                    if gt_context.metadata.get(context_type, None):
                        count += 1
                self.metadata[context_type] = count

    def set_response(self, response: str):
        self.response = response
        # if self.ground_truth:
        #     self.metadata = self.cal_metric(self.query, self.ground_truth, response)

    def append_gt_contexts(self, new_gts: List[ContextGT],) -> dict:
        if self.gt_contexts is None:
            self.gt_contexts = []

        existing_node_ids = {c.node_id for c in self.gt_contexts if c.node_id}
        added = 0
        skipped_ids = []
        for gt in new_gts:
            if gt.node_id and gt.node_id in existing_node_ids:
                skipped_ids.append(gt.node_id)
                continue

            self.gt_contexts.append(gt)
            added += 1
            if gt.node_id:
                existing_node_ids.add(gt.node_id)

        self.init_context_idx(ContextType.GT)
        return {
            'added': added,
            'skipped_duplicates': set(skipped_ids),
            'total_gt_contexts': len(self.gt_contexts)
        }

    @classmethod
    def check_parts_in_text(cls, gt_context, text, threshold):
        if threshold < 1:
            return fuzzy_contains(gt_context, text, threshold)
        else:
            parts = gt_context.split()
            return all(part in text for part in parts)

    @classmethod
    def check_annotation_gt_match(cls, gt: ContextGT, candidate_context: ContextItem):
        # Primary matching: node_id comparison (most accurate)
        if (candidate_context.node_id and gt.node_id and
                candidate_context.node_id == gt.node_id):
            return True
        # Secondly matching: context comparsion
        candidate_content = candidate_context.text.strip()
        gt_content = gt.node_text.strip()
        return candidate_content == gt_content

    @classmethod
    def check_traditional_gt_match(cls, gt: ContextGT, candidate_context: ContextItem, threshold: float = 1.0,enable_fuzzy=False, confidence_topn=5) -> bool:
        # First check file name matching if both are available
        file_match = True
        if candidate_context.file_name and gt.file_name and gt.file_name != "":
            file_match = gt.file_name in candidate_context.file_name

        if not file_match:
            return False
        default_matcher.update_settings(similarity_threshold=threshold,enable_fuzzy=enable_fuzzy, confidence_topn=confidence_topn)
        match_type, confidence = default_matcher.match_texts(candidate_context.text, gt.text)
        # Consider exact matches and high-confidence partial matches
        if match_type == "exact":
            return True
        elif match_type == "partial":
            return True

    @classmethod
    def context_matches_gt(cls, gt_contexts: List[ContextGT], candidate_context: ContextItem, context_type: ContextType, threshold=1, enable_fuzzy=False, confidence_topn=5):
        hit_indices = []
        for gt in gt_contexts:
            matched = False
            if gt.gt_type == GTType.ANNOTATION:
                matched = cls.check_annotation_gt_match(gt, candidate_context)
            else:
                matched = cls.check_traditional_gt_match(gt, candidate_context, threshold, enable_fuzzy, confidence_topn)

            if matched:
                gt.metadata = gt.metadata or {}
                retrieved_list = gt.metadata.get(context_type, [])
                retrieved_list.append(candidate_context.context_idx)
                gt.metadata[context_type] = retrieved_list
                hit_indices.append(gt.context_idx)

        if hit_indices:
            candidate_context.metadata = candidate_context.metadata or {}
            prev_hit = candidate_context.metadata.get("hit", [])
            if not isinstance(prev_hit, list):
                prev_hit = [prev_hit]
            candidate_context.metadata["hit"] = list(set(prev_hit + hit_indices))
            return True
        return False

    @classmethod
    def cal_metric(cls, query: str, ground_truth: str, response: str) -> Dict[str, float]:
        # Placeholder: Use actual metric calculations as needed.
        accuracy = float(ground_truth in response)
        return {"accuracy": accuracy}


class RAGResults(BaseModel):
    metadata: Optional[Dict[str, Union[float, int]]] = None
    results: List[RAGResult] = []
    finished: bool = False

    def add_result(self, result):
        # if result.query_id has appear in self.results, then update the result,else append the results
        updated_existing = False
        if result.query_id is not None:
            for idx, r in enumerate(self.results):
                if r.query_id == result.query_id:
                    self.results[idx] = result
                    updated_existing = True
                    break
        if not updated_existing:
            self.results.append(result)
        self.cal_metadata()

    def cal_recall(self):
        recall_rates = {}
        for context_type in [ContextType.RETRIEVAL, ContextType.POSTPROCESSING]:
            hit_count = 0
            gt_count = 0
            for result in self.results:
                gt_count += len(result.gt_contexts) if result.gt_contexts else 0
                hit_count += result.metadata.get(context_type, 0) if result.metadata else 0

            recall_rate = hit_count / gt_count if gt_count > 0 else np.nan
            if context_type is ContextType.RETRIEVAL:
                recall_rates[Metrics.RETRIEVAL_RECALL.value] = recall_rate
            elif context_type is ContextType.POSTPROCESSING:
                recall_rates[Metrics.POSTPROCESSING_RECALL.value] = recall_rate
        self.metadata = self.metadata or {}
        self.metadata.update(recall_rates)

    def cal_metadata(self):
        self.cal_recall()

        rate_sums = {}
        rate_counts = {}

        for result in self.results:
            if not result.metadata:
                continue
            for key, value in result.metadata.items():
                if isinstance(value, (int, float)) and key in {metric.value for metric in Metrics}:
                    if key not in rate_sums:
                        rate_sums[key] = 0.0
                        rate_counts[key] = 0
                    rate_sums[key] += value
                    rate_counts[key] += 1

        self.metadata = self.metadata or {}
        for key, total in rate_sums.items():
            avg = total / rate_counts[key] if rate_counts[key] > 0 else np.nan
            self.metadata[f"{key}"] = avg

    def get_metrics(self):
        return self.metadata or {}

    def get_metric(self, metric: Metrics, default=float("-inf")):
        return (self.metadata or {}).get(metric.value, default)

    def update_result_metrics(self, query_id: int, metrics: Dict[str, Union[float, int]]):
        updated = False
        for result in self.results:
            if result.query_id == query_id:
                result.update_metrics(metrics)
                updated = True
                break

        if updated:
            self.cal_metadata()
        return updated

    def check_metadata(self):
        if not self.metadata:
            print("No metadata found.")
            return
        for key, value in self.metadata.items():
            print(f"{key}: {value}")

    def save_to_json(self, file_path: str):
        cleaned_metadata = {str(k): v for k, v in (self.metadata or {}).items()}
        rag_results_dict = {
            **self.dict(exclude={"metadata"}),
            "metadata": cleaned_metadata,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rag_results_dict, f, ensure_ascii=False, indent=4)

    def save_to_csv(self, output_dir: str):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # --- CSV 1: Contexts ---
        contexts_csv = output_dir / "rag_contexts.csv"
        with contexts_csv.open("w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["query_id", "context_type", "context_idx", "file_name", "text"]
            metadata_keys = set()
            for result in self.results:
                for context_type in ContextType:
                    context_list = getattr(result, f"{context_type.value}_contexts") or []
                    for ctx in context_list:
                        if ctx.metadata:
                            metadata_keys.update(ctx.metadata.keys())
            fieldnames.extend(metadata_keys)
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                for context_type in ContextType:
                    context_list = getattr(result, f"{context_type.value}_contexts") or []
                    for ctx in context_list:
                        row = {
                            "query_id": result.query_id,
                            "context_type": f"{context_type.value}_contexts",
                            "context_idx": ctx.context_idx,
                            "file_name": ctx.file_name,
                            "text": ctx.text,
                        }
                        if ctx.metadata:
                            for key in metadata_keys:
                                row[key] = ctx.metadata.get(key, "")
                        writer.writerow(row)

        # --- CSV 2: Summary ---
        summary_csv = output_dir / "rag_summary.csv"
        with summary_csv.open("w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["query_id", "query", "ground_truth", "response", "gt_count"]
            metadata_keys = set()
            for result in self.results:
                if result.metadata:
                    metadata_keys.update(result.metadata.keys())
            fieldnames.extend(metadata_keys)

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                row = {
                    "query_id": result.query_id,
                    "query": result.query,
                    "ground_truth": result.ground_truth,
                    "response": result.response,
                    "gt_count": len(result.gt_contexts),
                }
                if result.metadata:
                    for key in metadata_keys:
                        row[key] = result.metadata.get(key, "")
                writer.writerow(row)
