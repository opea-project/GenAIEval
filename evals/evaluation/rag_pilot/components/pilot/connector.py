# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests
from components.pilot.base import convert_dict_to_pipeline
from components.pilot.ecrag.api_schema import PipelineCreateIn, RagOut

ECRAG_SERVICE_HOST_IP = os.getenv("ECRAG_SERVICE_HOST_IP", "127.0.0.1")
ECRAG_SERVICE_PORT = int(os.getenv("ECRAG_SERVICE_PORT", 16010))
server_addr = f"http://{ECRAG_SERVICE_HOST_IP}:{ECRAG_SERVICE_PORT}"


def get_active_pipeline() -> PipelineCreateIn:
    path = "/v1/settings/pipelines"
    res = requests.get(f"{server_addr}{path}", proxies={"http": None})
    if res.status_code == 200:
        for pl in res.json():
            if pl["status"]["active"]:
                return convert_dict_to_pipeline(pl)
    return None


def update_pipeline(pipeline_conf):
    path = "/v1/settings/pipelines"
    return requests.patch(
        f"{server_addr}{path}/{pipeline_conf.name}", json=pipeline_conf.dict(), proxies={"http": None}
    )


def get_ragqna(query):
    new_req = {"messages": query}
    path = "/v1/ragqna"
    res = requests.post(f"{server_addr}{path}", json=new_req, proxies={"http": None})
    if res.status_code == 200:
        return RagOut(**res.json())
    else:
        return None


def reindex_data():
    path = "/v1/data"
    res = requests.post(f"{server_addr}{path}/reindex", proxies={"http": None})
    return res.status_code == 200


def update_active_pipeline(pipeline):
    pipeline.active = False
    res = update_pipeline(pipeline)
    if res.status_code == 200:
        pipeline.active = True
        res = update_pipeline(pipeline)
    return res.status_code == 200


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
