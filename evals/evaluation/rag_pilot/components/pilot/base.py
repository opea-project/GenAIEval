# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import hashlib
import json
import re
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from copy import deepcopy
import yaml


def dynamically_find_function(key: str, target_dict: Dict) -> Callable:
    if key in target_dict:
        instance, attr_expression = target_dict[key]
        if "[" in attr_expression and "]" in attr_expression:
            attr_name, index = attr_expression[:-1].split("[")
            index = int(index)
            func = getattr(instance, attr_name)
            if isinstance(func, list) and 0 <= index < len(func):
                func = func[index]
            else:
                raise ValueError(f"Attribute '{attr_name}' is not a list or index {index} is out of bounds")
        elif attr_expression == "":
            func = instance
        else:
            func = getattr(instance, attr_expression)
        return func
    else:
        print(f"Input module or node '{key}' is not supported.")


def get_support_modules(type_name: str, module_map: Dict[str, Callable]) -> Optional[Callable]:
    support_modules = module_map
    return dynamically_find_function(type_name, support_modules)


class ModuleBase(BaseModel):
    type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    func: Optional[Callable] = None
    is_active: bool = False

    @classmethod
    def from_dict(cls, component_dict: Dict) -> "ModuleBase":
        _component_dict = deepcopy(component_dict)
        type_ = _component_dict.pop("type")
        params = _component_dict
        return cls(type=type_, params=params)

    def update_func(self, module_map: Dict[str, Callable]):
        self.func = get_support_modules(self.type, module_map)
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")

    def get_params(self, attr: str):
        return self.params.get(attr)

    def get_status(self) -> bool:
        return self.is_active

    def get_value(self, attr: str):
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")
            return None
        return getattr(self.func, attr, None)

    def set_value(self, attr: str, value: Any):
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")
        else:
            setattr(self.func, attr, value)


class Attribute(ModuleBase):
    @classmethod
    def from_dict(cls, attr_dict: Dict) -> "Attribute":
        _attr_dict = deepcopy(attr_dict)
        type_ = _attr_dict.pop("type")
        params = _attr_dict.pop("params", {})
        return cls(type=type_, params=params)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "params": self.params
        }


class Module(ModuleBase):
    attributes: List[Attribute] = Field(default_factory=list)

    @field_validator("attributes", mode="before")
    @classmethod
    def validate_attributes(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise TypeError("attributes must be a list")
        return [a if isinstance(a, Attribute) else Attribute.model_validate(a) for a in v]

    @classmethod
    def from_dict(cls, module_dict: Dict) -> "Module":
        _module_dict = deepcopy(module_dict)
        type_ = _module_dict.pop("type")
        params = _module_dict.pop("params", {})
        attributes_list = _module_dict.pop("attributes", [])
        atrributes = []
        if attributes_list is not None:
            attributes = [Attribute.from_dict(value) for value in attributes_list]
        return cls(type=type_, params=params, attributes=attributes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "params": self.params,
            "attributes": [a.to_dict() for a in self.attributes]
        }


class Node(ModuleBase):
    modules: List[Module] = Field(default_factory=list)

    @field_validator("modules", mode="before")
    @classmethod
    def validate_modules(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise TypeError("modules must be a list of Module")
        return [m if isinstance(m, Module) else Module.model_validate(m) for m in v]

    @classmethod
    def from_dict(cls, node_dict: Dict) -> "Node":
        type_ = node_dict.get("type")
        params = node_dict.get("params", {})
        modules_list = node_dict.get("modules", [])
        modules = []
        if modules_list is not None:
            modules = [Module.from_dict(m) for m in modules_list]
        return cls(type=type_, params=params, modules=modules)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Node":
        with open(yaml_path, "r") as f:
            node_dict = yaml.safe_load(f)
        return cls.from_dict(node_dict)

    def get_params(self, attr: str):
        if attr in self.params:
            return self.params[attr]
        elif attr.endswith("type"):
            return [m.type for m in self.modules]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "params": self.params,
            "modules": [m.to_dict() for m in self.modules]
        }

    def to_yaml(self, yaml_path: str) -> None:
        with open(yaml_path, "w") as f:
            yaml.dump(self.to_dict(), f, sort_keys=False)


def generate_json_id(config, length=8) -> int:
    if "active" in config:
        del config["active"]
    if "name" in config:
        del config["name"]
    config_str = json.dumps(config, sort_keys=True)
    unique_id = hashlib.sha256(config_str.encode()).hexdigest()
    return int(unique_id[:length], 16)


class ContextType(str, Enum):
    GT = "gt"
    RETRIEVAL = "retrieval"
    POSTPROCESSING = "postprocessing"


class GTType(str, Enum):
    TRADITIONAL = "traditional"
    ANNOTATION = "annotation"


class ContextItem(BaseModel):
    context_idx: Optional[int] = None
    node_id: Optional[str] = None
    file_name: Optional[str] = None
    text: str = ""
    metadata: Optional[Dict[str, Union[float, int, list]]] = {}


class ContextGT(BaseModel):
    context_idx: Optional[int] = None
    file_name: Optional[str] = None
    node_id: Optional[str] = None  # Changed from int to str to match NodeInfo
    node_text: str = ""
    text: str = ""
    metadata: Optional[Dict[str, Union[float, int, list]]] = {}
    page_label: Optional[str] = None
    gt_type: GTType = GTType.TRADITIONAL


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
