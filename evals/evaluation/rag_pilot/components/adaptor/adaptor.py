# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
import yaml


class AdaptorBase(ABC):

    def __init__(self, spec_file: str):
        self.spec = {}
        self.server_addr = ""

        if spec_file:
            """Load a complete pipeline from YAML file."""
            with open(spec_file, 'r') as f:
                for doc in yaml.safe_load_all(f):
                    self.spec.update(doc)
            if not self.spec:
                raise ValueError("No recognized nodes found in the YAML file")

    @abstractmethod
    def get_active_pipeline():
        pass

    @abstractmethod
    def apply_pipeline():
        pass
