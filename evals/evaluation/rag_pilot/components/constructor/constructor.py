# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Dict
import json
import copy

from components.constructor.ecrag.api_schema import (
    NodeParserIn, IndexerIn, RetrieverIn, PostProcessorIn, GeneratorIn,
    ModelIn, PipelineCreateIn
)


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
        node_parser=initialize_component(
            NodeParserIn,
            pl.get("node_parser"),
            key_map={"idx": "idx"}
        ),
        indexer=initialize_component(
            IndexerIn,
            pl.get("indexer"),
            key_map={"model": "embedding_model", "idx": "idx"},
            nested_fields={"embedding_model": ModelIn}
        ),
        retriever=initialize_component(
            RetrieverIn,
            pl.get("retriever"),
            key_map={"idx": "idx"}
        ),
        postprocessor=[
            initialize_component(
                PostProcessorIn,
                pp,
                extra={"processor_type": pp.get("processor_type")},
                key_map={"model": "reranker_model", "idx": "idx"},
                nested_fields={"reranker_model": ModelIn}
            )
            for pp in pl.get("postprocessor", [])
        ],
        generator=initialize_component(
            GeneratorIn,
            pl.get("generator"),
            key_map={"idx": "idx"},
            nested_fields={"model": ModelIn}
        ),
        active=pl.get("status", {}).get("active", False)
    )


class Constructor:

    def __init__(self):
        self.pl: Optional[PipelineCreateIn] = None
        self._backup = None

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
                model_type=model_type,
                model_id=model_id,
                model_path=model_path,
                weight=weight,
                device=device
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

    def set_pipeline(self, pl):
        self.pl = pl
        self._replace_model_with_id()

    def export_pipeline(self):
        self._restore_model_instances()
        exported_pl  = copy.deepcopy(self.pl)
        self._replace_model_with_id()
        return exported_pl

    def activate_pl(self):
        self.pl.active = True

    def deactivate_pl(self):
        self.pl.active = False

    def save_pipeline_to_json(self, save_path = "pipeline.json"):
        if self.pl:
            pipeline_dict = self.export_pipeline().dict()
            with open(save_path, "w") as json_file:
                json.dump(pipeline_dict, json_file, indent=4)
            print(f'RAG pipeline is successfully exported to "{save_path}"')


def get_ecrag_module_map(ecrag_pl):
    ecrag_modules = {
        # root
        "root": (ecrag_pl, ""),
        # node_parser
        "node_parser": (ecrag_pl, "node_parser"),
        "simple": (ecrag_pl, "node_parser"),
        "hierarchical": (ecrag_pl, "node_parser"),
        "sentencewindow": (ecrag_pl, "node_parser"),
        # indexer
        "indexer": (ecrag_pl, "indexer"),
        "vector": (ecrag_pl, "indexer"),
        "faiss_vector": (ecrag_pl, "indexer"),
        # retriever
        "retriever": (ecrag_pl, "retriever"),
        "vectorsimilarity": (ecrag_pl, "retriever"),
        "auto_merge": (ecrag_pl, "retriever"),
        "bm25": (ecrag_pl, "retriever"),
        # postprocessor
        "postprocessor": (ecrag_pl, "postprocessor[0]"),
        "reranker": (ecrag_pl, "postprocessor[0]"),
        "metadata_replace": (ecrag_pl, "postprocessor[0]"),
        # generator
        "generator": (ecrag_pl, "generator"),
    }
    return ecrag_modules


COMP_TYPE_MAP = {
    "node_parser": "parser_type",
    "indexer": "indexer_type",
    "retriever": "retriever_type",
    "postprocessor": "processor_type",
    "generator": "inference_type",
}
