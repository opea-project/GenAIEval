# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC
from typing import Dict, List, Any
import yaml
import uuid

from components.pilot.base import Node


class Pipeline(ABC):

    def __init__(self, ptype: str = "", Nodes: List[Node] = [], uid: uuid.UUID = None):
        self.type: str = ptype
        self.nodes: List[Node] = Nodes
        if uid:
            self.id = uid
        else:
            self.id = uuid.uuid4()

    def get_id(self):
        return self.id

    def regenerate_id(self):
        self.id = uuid.uuid4()

    def to_dict(self) -> Dict[str, Any]:
        """Convert RAGPipeline to dictionary representation."""
        pipeline = {}
        pipeline["type"] = self.type
        pipeline["id"] = self.id
        for n in self.nodes:
            pipeline[n.type] = {}
            for m in n.modules:
                pipeline[n.type][m.type] = {}
                for a in m.attributes:
                    if "value" in a.params:
                        pipeline[n.type][m.type][a.type] = a.params["value"]

        return pipeline


class RAGPipelineTemplate(Pipeline):
    def __init__(self, config_file="configs/RAGPipeline.yaml"):
        ragnodes = []
        if config_file:
            """Load a complete pipeline from YAML file."""
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)

            nodes_config = config.get('nodes', [])
            if not nodes_config:
                raise ValueError("No nodes found in the YAML file")
            for n in nodes_config:
                ragnodes.append(Node.from_dict(n))

        else:
            # Fallback to default rag nodes
            ragnodes = [
                Node(type="node_parser"),
                Node(type="indexer"),
                Node(type="retriever"),
                Node(type="postprocessor"),
                Node(type="generator")
            ]

        super().__init__("RAG", ragnodes)
