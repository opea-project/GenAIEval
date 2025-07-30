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

from components.pilot.ecrag.api_schema import (
    GeneratorIn,
    IndexerIn,
    ModelIn,
    NodeParserIn,
    PipelineCreateIn,
    PostProcessorIn,
    RetrieverIn,
)


class Metrics(str, Enum):
    RETRIEVAL_RECALL = "retrieval_recall_rate"
    POSTPROCESSING_RECALL = "postprocessing_recall_rate"
    ANSWER_RELEVANCY = "answer_relevancy"


def convert_dict_to_pipeline(pl: dict) -> PipelineCreateIn:
    def initialize_component(cls, data, extra=None, key_map=None, nested_fields=None):
        if not data:
            return None

        extra = extra or {}
        key_map = key_map or {}
        nested_fields = nested_fields or {}

        processed_data = {}
        for k, v in data.items():
            mapped_key = key_map.get(k, k)
            if mapped_key in nested_fields:
                processed_data[mapped_key] = initialize_component(nested_fields[mapped_key], v)
            else:
                processed_data[mapped_key] = v
        if cls == ModelIn:
            processed_data["model_type"] = data.get("type", processed_data.get("model_type"))

        processed_data.update(extra)
        return cls(**processed_data)

    return PipelineCreateIn(
        idx=pl.get("idx"),
        name=pl.get("name"),
        node_parser=initialize_component(NodeParserIn, pl.get("node_parser"), key_map={"idx": "idx"}),
        indexer=initialize_component(
            IndexerIn,
            pl.get("indexer"),
            key_map={"model": "embedding_model", "idx": "idx"},
            nested_fields={"embedding_model": ModelIn},
        ),
        retriever=initialize_component(RetrieverIn, pl.get("retriever"), key_map={"idx": "idx"}),
        postprocessor=[
            initialize_component(
                PostProcessorIn,
                pp,
                extra={"processor_type": pp.get("processor_type")},
                key_map={"model": "reranker_model", "idx": "idx"},
                nested_fields={"reranker_model": ModelIn},
            )
            for pp in pl.get("postprocessor", [])
        ],
        generator=initialize_component(
            GeneratorIn, pl.get("generator"), key_map={"idx": "idx"}, nested_fields={"model": ModelIn}
        ),
        active=pl.get("status", {}).get("active", False),
    )


def generate_json_id(config, length=8) -> int:
    if "active" in config:
        del config["active"]
    if "name" in config:
        del config["name"]
    config_str = json.dumps(config, sort_keys=True)
    unique_id = hashlib.sha256(config_str.encode()).hexdigest()
    return int(unique_id[:length], 16)


class RAGPipeline(BaseModel):
    pl: PipelineCreateIn
    id: int = Field(default=0)
    _backup: Dict = {}

    def __init__(self, pl):
        super().__init__(pl=pl)
        self._replace_model_with_id()
        # self.id = generate_json_id(self.pl.dict())
        self.id = uuid.uuid4()

    def _replace_model_with_id(self):
        self._backup = {}

        def extract_model_id(model):
            if model:
                if model.model_type not in self._backup:
                    self._backup[model.model_type] = []
                self._backup[model.model_type].append(model)
                return model.model_id
            return None

        if self.pl.indexer and self.pl.indexer.embedding_model:
            self.pl.indexer.embedding_model = extract_model_id(self.pl.indexer.embedding_model)

        if self.pl.postprocessor:
            for proc in self.pl.postprocessor:
                if proc.reranker_model:
                    proc.reranker_model = extract_model_id(proc.reranker_model)

        if self.pl.generator and self.pl.generator.model:
            self.pl.generator.model = extract_model_id(self.pl.generator.model)

    def _restore_model_instances(self):
        if not self._backup:
            self._backup = {}

        def restore_model(model_id, model_type, is_generator=False):
            if model_type in self._backup:
                for existing_model in self._backup[model_type]:
                    if existing_model.model_id == model_id:
                        return existing_model

                weight = self._backup[model_type][0].weight
                device = self._backup[model_type][0].device
            else:
                weight = "INT4" if is_generator else ""
                device = "auto"

            model_path = f"./models/{model_id}"
            if is_generator:
                model_path += f"/{weight}_compressed_weights"

            return ModelIn(
                model_type=model_type, model_id=model_id, model_path=model_path, weight=weight, device=device
            )

        if self.pl.indexer and isinstance(self.pl.indexer.embedding_model, str):
            self.pl.indexer.embedding_model = restore_model(self.pl.indexer.embedding_model, "embedding")

        if self.pl.postprocessor:
            for proc in self.pl.postprocessor:
                if isinstance(proc.reranker_model, str):
                    proc.reranker_model = restore_model(proc.reranker_model, "reranker")

        if self.pl.generator and isinstance(self.pl.generator.model, str):
            self.pl.generator.model = restore_model(self.pl.generator.model, "llm", is_generator=True)

        self._backup = None

    def get_prompt(self) -> Optional[str]:
        generator = self.pl.generator
        if not generator:
            return None
        if generator.prompt_content:
            return generator.prompt_content
        # if generator.prompt_path:
        #     try:
        #         with open(generator.prompt_path, 'r', encoding='utf-8') as f:
        #             return f.read()
        #     except FileNotFoundError:
        #         raise FileNotFoundError(f"Prompt file not found at path: {generator.prompt_path}")
        #     except Exception as e:
        #         raise RuntimeError(f"Error reading prompt from {generator.prompt_path}: {e}")
        return None

    def export_pipeline(self):
        self._restore_model_instances()
        exported_pl = copy.deepcopy(self.pl)
        self._replace_model_with_id()
        return exported_pl

    @model_serializer(mode="plain")
    def ser_model(self):
        return {
            "id": self.id,
            **self.pl.model_dump()
        }

    def copy(self):
        return copy.deepcopy(self)

    def get_id(self):
        return self.id

    def regenerate_id(self):
        # self.id = generate_json_id(self.pl.dict())
        self.id = uuid.uuid4()

    def activate_pl(self):
        self.pl.active = True

    def deactivate_pl(self):
        self.pl.active = False

    def save_to_json(self, save_path="pipeline.json"):
        if self.pl:
            pipeline_dict = self.export_pipeline().dict()
            with open(save_path, "w") as json_file:
                json.dump(pipeline_dict, json_file, indent=4)
            # print(f'RAG pipeline is successfully exported to "{save_path}"')


class ContextType(str, Enum):
    GT = "gt"
    RETRIEVAL = "retrieval"
    POSTPROCESSING = "postprocessing"


class ContextItem(BaseModel):
    context_idx: Optional[int] = None
    file_name: Optional[str] = None
    text: str = ""
    metadata: Optional[Dict[str, Union[float, int, list]]] = {}


def normalize_text(text):
    """Removes whitespace and English/Chinese punctuation from text for fair comparison."""
    return re.sub(r"[ \u3000\n\t，。！？；：“”‘’\"',.;!?()\[\]{}<>《》|]+", "", text)


def split_text(text):
    """
    Splits text into tokens using a robust regex that handles:
    - Whitespace (\n, \t, space)
    - English and Chinese punctuation
    - Markdown/table symbols like '---|---' and ' | '
    """
    return [t for t in re.split(r"(?:\s*\|+\s*|[ \u3000\n\t，。！？；：“”‘’\"',.;!?()\[\]{}<>《》]+|---+)", text) if t]


def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def fuzzy_contains(needle, haystack, threshold):
    needle_norm = normalize_text(needle)
    tokens = split_text(haystack)

    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens) + 1):
            subtext = "".join(tokens[i:j])
            subtext_norm = normalize_text(subtext)
            score = calculate_similarity(needle_norm, subtext_norm)
            if score >= threshold:
                return True
    return False


class RAGResult(BaseModel):
    metadata: Optional[Dict[str, Union[float, int, list]]] = {}
    query_id: Optional[int] = None
    query: str
    ground_truth: Optional[str] = None
    response: Optional[str] = None

    gt_contexts: Optional[List[ContextItem]] = None
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

    def update_metadata_hits(self, threshold=1):
        if self.gt_contexts:
            for context_type in [ContextType.RETRIEVAL, ContextType.POSTPROCESSING]:
                context_list_name = f"{context_type.value}_contexts"
                context_list = getattr(self, context_list_name, None)
                if context_list is None:
                    continue
                for context in context_list:
                    self.context_matches_gt(self.gt_contexts, context, context_type, threshold)

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

    @classmethod
    def check_parts_in_text(cls, gt_context, text, threshold):
        if threshold < 1:
            return fuzzy_contains(gt_context, text, threshold)
        else:
            parts = gt_context.split()
            return all(part in text for part in parts)

    @classmethod
    def context_matches_gt(
        cls, gt_contexts: List[ContextItem], candidate_context: ContextItem, context_type: ContextType, threshold
    ):
        for gt in gt_contexts:
            if (
                candidate_context.file_name and gt.file_name and gt.file_name in candidate_context.file_name
            ) or gt.file_name == "":
                if candidate_context.text in gt.text or cls.check_parts_in_text(
                    gt.text, candidate_context.text, threshold
                ):
                    gt.metadata = gt.metadata or {}
                    retrieved_file_name_list = gt.metadata.get(context_type, [])
                    retrieved_file_name_list.append(candidate_context.context_idx)
                    gt.metadata[context_type] = retrieved_file_name_list

                    candidate_context.metadata = candidate_context.metadata or {}
                    candidate_context.metadata["hit"] = gt.context_idx
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
        #if result.query_id has appear in self.results, then update the result,else append the results
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
