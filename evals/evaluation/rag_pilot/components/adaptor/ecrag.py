# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import json
import uuid
from enum import Enum
from typing import Any, Optional
from typing import List
from llama_index.core.schema import TextNode
from pydantic import BaseModel
from components.adaptor.adaptor import AdaptorBase
from components.pilot.pipeline import Pipeline
from components.pilot.base import Node, Module, Attribute
import requests
from urllib.parse import quote

ECRAG_SERVICE_HOST_IP = os.getenv("ECRAG_SERVICE_HOST_IP", "127.0.0.1")
ECRAG_SERVICE_PORT = int(os.getenv("ECRAG_SERVICE_PORT", 16010))
server_addr = f"http://{ECRAG_SERVICE_HOST_IP}:{ECRAG_SERVICE_PORT}"


class CompType(str, Enum):

    DEFAULT = "default"
    MODEL = "model"
    PIPELINE = "pipeline"
    NODEPARSER = "node_parser"
    INDEXER = "indexer"
    RETRIEVER = "retriever"
    POSTPROCESSOR = "postprocessor"
    GENERATOR = "generator"
    FILE = "file"


class ModelType(str, Enum):

    EMBEDDING = "embedding"
    RERANKER = "reranker"
    LLM = "llm"
    VLLM = "vllm"


class FileType(str, Enum):
    TEXT = "text"
    VISUAL = "visual"
    AURAL = "aural"
    VIRTUAL = "virtual"
    OTHER = "other"


class NodeParserType(str, Enum):

    SIMPLE = "simple"
    HIERARCHY = "hierarchical"
    SENTENCEWINDOW = "sentencewindow"
    UNSTRUCTURED = "unstructured"


class IndexerType(str, Enum):

    FAISS_VECTOR = "faiss_vector"
    DEFAULT_VECTOR = "vector"
    MILVUS_VECTOR = "milvus_vector"


class RetrieverType(str, Enum):

    VECTORSIMILARITY = "vectorsimilarity"
    AUTOMERGE = "auto_merge"
    BM25 = "bm25"


class PostProcessorType(str, Enum):

    RERANKER = "reranker"
    METADATAREPLACE = "metadata_replace"


class GeneratorType(str, Enum):

    CHATQNA = "chatqna"


class InferenceType(str, Enum):

    LOCAL = "local"
    VLLM = "vllm"


class CallbackType(str, Enum):

    DATAPREP = "dataprep"
    RETRIEVE = "retrieve"
    PIPELINE = "pipeline"


class ModelIn(BaseModel):
    model_type: Optional[str] = "LLM"
    model_id: Optional[str]
    model_path: Optional[str] = "./"
    weight: Optional[str] = "INT4"
    device: Optional[str] = "cpu"


class NodeParserIn(BaseModel):
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_sizes: Optional[list] = None
    parser_type: str
    window_size: Optional[int] = 3


class IndexerIn(BaseModel):
    indexer_type: str
    embedding_model: Optional[ModelIn] = None
    embedding_url: Optional[str] = None
    vector_url: Optional[str] = None


class RetrieverIn(BaseModel):
    retriever_type: str
    retrieve_topk: Optional[int] = 3


class PostProcessorIn(BaseModel):
    processor_type: str
    reranker_model: Optional[ModelIn] = None
    top_n: Optional[int] = 5


class GeneratorIn(BaseModel):
    prompt_path: Optional[str] = None
    prompt_content: Optional[str] = None
    model: Optional[ModelIn] = None
    inference_type: Optional[str] = "local"
    vllm_endpoint: Optional[str] = None


class PipelineCreateIn(BaseModel):
    name: Optional[str] = None
    node_parser: Optional[NodeParserIn] = None
    indexer: Optional[IndexerIn] = None
    retriever: Optional[RetrieverIn] = None
    postprocessor: Optional[list[PostProcessorIn]] = None
    generator: Optional[GeneratorIn] = None
    active: Optional[bool] = False


class DataIn(BaseModel):
    text: Optional[str] = None
    local_path: Optional[str] = None


class FilesIn(BaseModel):
    local_paths: Optional[list[str]] = None


class RagOut(BaseModel):
    query: str
    contexts: Optional[dict[str, Any]] = None
    response: str


class PromptIn(BaseModel):
    prompt: Optional[str] = None


class KnowledgeBaseCreateIn(BaseModel):
    name: str
    description: Optional[str] = None
    active: Optional[bool] = None
    comp_type: Optional[str] = "knowledge"
    comp_subtype: Optional[str] = "origin_kb"
    experience_active: Optional[bool] = None


class ExperienceIn(BaseModel):
    question: str
    content: list[str] = None


class MilvusConnectRequest(BaseModel):
    vector_url: str


class ECRAGAdaptor(AdaptorBase):
    def __init__(self, config_file="configs/ecrag.yaml"):
        super().__init__(config_file)
        self.server_addr = server_addr

    def set_server_addr(self, cur_server_addr: str):
        self.server_addr = cur_server_addr

    def test(self):
        path = "/v1/settings/pipelines"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})
        if res.status_code == 200:
            return True
        return False

    def get_active_pipeline(self) -> Pipeline:
        pl = self.get_active_pipeline_ecrag()
        if pl:
            return self.convert_ecrag_schema_to_pipeline(pl)
        else:
            return None

    def get_active_pipeline_ecrag(self) -> dict:
        path = "/v1/settings/pipelines"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})
        if res.status_code == 200:
            for pl in res.json():
                if pl["status"]["active"]:
                    active_pl = self.get_pipeline_ecrag(pl["name"])
                    # active_pl["generator"]["prompt_content"] = self.get_prompt()
                    return active_pl
        return None

    def get_pipeline_ecrag(self, name) -> dict:
        path = f"/v1/settings/pipelines/{name}/json"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})
        if res.status_code == 200:
            return json.loads(res.json())
        return None

    def apply_pipeline(self, tgt_pl: Pipeline):
        ecrag_pl = self.get_active_pipeline_ecrag()
        if tgt_pl is not None and len(tgt_pl.nodes) > 0:
            ecrag_pl = self.update_ecrag_pipeline_conf(ecrag_pl, tgt_pl)
            self.update_active_pipeline(ecrag_pl)

    def get_ragqna(self, query):
        new_req = {"messages": query, "stream": True}
        path = "/v1/ragqna"
        res = requests.post(f"{self.server_addr}{path}", json=new_req, proxies={"http": None})
        if res.status_code == 200:
            return RagOut(**res.json())
        else:
            return None

    def get_retrieval(self, query):
        new_req = {"messages": query}
        path = "/v1/retrieval"
        res = requests.post(f"{self.server_addr}{path}", json=new_req, proxies={"http": None})
        if res.status_code == 200:
            return RagOut(**res.json())
        else:
            return None

    def update_active_pipeline(self, pipeline):
        pipeline["active"] = False
        res = self.update_pipeline(pipeline)
        if res.status_code == 200:
            pipeline["active"] = True
            res = self.update_pipeline(pipeline)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    def create_pipeline(self, pipeline_conf):
        path = "/v1/settings/pipelines"
        return requests.post(
            f"{self.server_addr}{path}", json=pipeline_conf, proxies={"http": None}
        )

    def update_pipeline(self, pipeline_conf):
        path = "/v1/settings/pipelines"
        pl_name = pipeline_conf["name"]
        return requests.patch(
            f"{self.server_addr}{path}/{pl_name}", json=pipeline_conf, proxies={"http": None}
        )

    def upload_files(self, file_conf):
        path = "/v1/data"
        return requests.post(
            f"{self.server_addr}{path}", json=file_conf.dict(), proxies={"http": None}
        )

    def get_prompt(self):
        path = "/v1/chatqna/prompt"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})

        if res.status_code == 200:
            return res.json()
        else:
            error_detail = res.text if hasattr(res, 'text') else "Unknown error"
            print(f"Failed to get prompt: {error_detail}")
            return False

    def get_default_prompt(self):
        path = "/v1/chatqna/prompt/default"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})

        if res.status_code == 200:
            return res.json()
        else:
            error_detail = res.text if hasattr(res, 'text') else "Unknown error"
            print(f"Failed to get default prompt: {error_detail}")
            return False

    def reindex_data(self):
        path = "/v1/data"
        res = requests.post(f"{self.server_addr}{path}/reindex", proxies={"http": None})
        return res.status_code == 200

    def update_ecrag_pipeline_conf(self, ecrag_pl: dict, target_pl: Pipeline) -> dict:
        print(f"[Pilot Adaptor] EC-RAG Configuration before tuning {ecrag_pl}")
        # target_pl.nodes is a List of Node object
        # self.spec is a Dict of Node dict??
        # TODO: consider align the types
        # Matching node type
        for pl_node in target_pl.nodes:
            for n_k, ecrag_node in self.spec.items():
                # Found node
                if pl_node.type == ecrag_node["type"]:
                    # Matching node type
                    for pl_m in pl_node.modules:
                        for ecrag_module in ecrag_node["modules"]:
                            # Found module ecrag_pl[n_k]
                            if pl_m.type == ecrag_module["type"]:
                                ecrag_pl = update_ecrag_module_dispatch(ecrag_pl, pl_m, n_k, ecrag_module)

        print(f"[Pilot Adaptor] EC-RAG Configuration after tuning {ecrag_pl}")
        return ecrag_pl

    # TODO: Finish the conversion
    def convert_ecrag_schema_to_pipeline(self, ecrag_pl: dict, uid: uuid.UUID = None) -> Pipeline:
        pl = Pipeline(uid)
        pl.type = "RAG"
        node_type = ["node_parser", "indexer", "retriever", "postprocessor", "generator"]
        if ecrag_pl:
            for n_type in node_type:
                node = convert_ecrag_schema_to_node(n_type, Node(type=n_type), ecrag_pl[n_type])
                pl.nodes.append(node)

        return pl

    def get_document_chunks(self, file_name: str) -> List[TextNode]:
        encoded_file_name = quote(file_name, safe='')
        # Use the actual EdgeCraftRAG API endpoint with properly encoded filename
        path = f"/v1/data/{encoded_file_name}/nodes"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})
        if res.status_code == 200:
            chunks_data = res.json()
            text_nodes = []
            print(f"[Pilot Adaptor] Received {len(chunks_data)} chunks of data for file: '{file_name}'")
            for i, chunk_data in enumerate(chunks_data):
                try:
                    text_node = TextNode(**chunk_data)
                    text_nodes.append(text_node)
                except Exception as e:
                    print(f"[Pilot Adaptor] ❌ Error creating TextNode from chunk_data[{i}]: {e}")
                    continue

            print(f"[Pilot Adaptor] Successfully created {len(text_nodes)} TextNode objects")
            return text_nodes
        else:
            print(f"[Pilot Adaptor] Failed to get document chunks for {file_name}: HTTP {res.status_code}")
            return []

    def get_available_documents(self):
        path = "/v1/data/documents"
        res = requests.get(f"{self.server_addr}{path}", proxies={"http": None})
        if res.status_code == 200:
            return res.json()
        else:
            print(f"Failed to get available documents: HTTP {res.status_code}")
            return {"total_documents": 0, "documents": []}


#
# Implementation of convert ecrag config to pipeline node object
# (ECRAG->Pipeline)
#
def convert_ecrag_schema_to_node(n_type, node, ecrag_comp):
    if n_type == "node_parser":
        if ecrag_comp["parser_type"] == NodeParserType.SIMPLE:
            node.modules.append(Module(
                type="direct",
                params={},
                attributes=[
                    Attribute(
                        type="chunk_size",
                        params={"value": ecrag_comp["chunk_size"]}
                    ),
                    Attribute(
                        type="chunk_overlap",
                        params={"value": ecrag_comp["chunk_overlap"]}
                    ),
                ]
            ))
    elif n_type == "indexer":
        node.modules.append(Module(
            type="embedding_model",
            params={},
            attributes=[
                Attribute(
                    type="model_name",
                    params={"value": ecrag_comp["embedding_model"]["model_id"]}
                ),
            ]
        ))
    elif n_type == "retriever":
        node.modules.append(Module(
            type="vectorsimilarity",
            params={},
            attributes=[
                Attribute(
                    type="top_k",
                    params={"value": ecrag_comp["retrieve_topk"]}
                ),
            ]
        ))
    elif n_type == "postprocessor":
        node.modules.append(Module(
            type="reranker",
            params={},
            attributes=[
                Attribute(
                    type="top_n",
                    # TODO: Consider reranker not the only postprocessor
                    params={"value": ecrag_comp[0]["top_n"]}
                ),
                Attribute(
                    type="model_name",
                    # TODO: Consider reranker not the only postprocessor
                    params={"value": ecrag_comp[0]["reranker_model"]["model_id"]}
                ),
            ]
        ))
    elif n_type == "generator":
        node.modules.append(Module(
            type="prompt",
            params={},
            attributes=[
                Attribute(
                    type="content",
                    params={"value": ecrag_comp["prompt_content"]}
                ),
            ]
        ))

    return node


#
# Apply new pipeline config to update ECRAG schema attributes
# Pipeline->ECRAG
#
def update_ecrag_module_dispatch(ecrag_pl: dict, target_module: Module, spec_node_name: str, spec_module: dict) -> dict:
    # Match attribute type
    for tgt_attr in target_module.attributes:
        for spec_attr in spec_module["attributes"]:
            if tgt_attr.type == spec_attr["type"]:
                # Update module values
                match spec_module["type"]:
                    case "direct":
                        ecrag_pl = update_ecrag_direct(ecrag_pl, tgt_attr, spec_node_name)
                    case "embedding_model":
                        ecrag_pl = update_ecrag_embedding_model(ecrag_pl, tgt_attr, spec_node_name, spec_module["type"])
                    case "vectorsimilarity":
                        ecrag_pl = update_ecrag_vectorsimilarity(ecrag_pl, tgt_attr, spec_node_name)
                    case "reranker":
                        ecrag_pl = update_ecrag_reranker(ecrag_pl, tgt_attr, spec_node_name)
                    case "prompt":
                        ecrag_pl = update_ecrag_prompt(ecrag_pl, tgt_attr, spec_node_name)
                    case _:
                        pass
    return ecrag_pl


#
# Implementation of updating ECRAG pipeline attributes
# (Pipeline->ECRAG schema)
#
def update_ecrag_direct(ecrag_pl: dict, target_attr: Attribute, spec_node_name: str) -> dict:
    node_parser = ecrag_pl[spec_node_name]
    if target_attr.type == "chunk_size":
        node_parser["chunk_size"] = target_attr.params["value"]
    if target_attr.type == "chunk_overlap":
        node_parser["chunk_overlap"] = target_attr.params["value"]
    return ecrag_pl


def update_ecrag_embedding_model(ecrag_pl: dict, target_attr: Attribute, spec_node_name: str, spec_module_name: str) -> dict:
    embedding_model = ecrag_pl[spec_node_name][spec_module_name]
    if target_attr.type == "model_name":
        embedding_model["model_id"] = target_attr.params["value"]
        embedding_model["model_path"] = "./models/" + target_attr.params["value"]
    return ecrag_pl


def update_ecrag_vectorsimilarity(ecrag_pl: dict, target_attr: Attribute, spec_node_name: str) -> dict:
    retriever = ecrag_pl[spec_node_name]
    if target_attr.type == "top_k":
        retriever["retrieve_topk"] = target_attr.params["value"]
    return ecrag_pl


def update_ecrag_reranker(ecrag_pl: dict, target_attr: Attribute, spec_node_name: str) -> dict:
    postprocessors = ecrag_pl[spec_node_name]
    for p in postprocessors:
        if p["processor_type"] == PostProcessorType.RERANKER:
            if target_attr.type == "top_n":
                p["top_n"] = target_attr.params["value"]
    return ecrag_pl


def update_ecrag_prompt(ecrag_pl: dict, target_attr: Attribute, spec_node_name: str) -> dict:
    generator = ecrag_pl[spec_node_name]
    if target_attr.type == "content":
        generator["prompt_content"] = target_attr.params["value"]
    return ecrag_pl
