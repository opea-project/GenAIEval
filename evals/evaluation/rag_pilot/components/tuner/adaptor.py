# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from components.pilot.base import RAGPipeline
from components.connect_utils import COMP_TYPE_MAP, get_ecrag_module_map


def get_support_modules(module_name: str, module_map) -> Callable:
    support_modules = module_map
    return dynamically_find_function(module_name, support_modules)


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


def convert_tuple(value):
    if isinstance(value, str):
        try:
            evaluated = ast.literal_eval(value)
            if isinstance(evaluated, tuple):
                if len(evaluated) == 2:
                    return Range(*evaluated)
                else:
                    return evaluated
        except (SyntaxError, ValueError):
            pass
    return value


class Range:
    def __init__(self, min_value: int, max_value: int):
        self.min = min_value
        self.max = max_value


class ModuleBase:
    def __init__(self, type: str, params: Dict[str, Any]):
        self.type: str = type
        self.params: Dict[str, Any] = params
        self.func: Optional[Callable] = None
        self.is_active = False

    @classmethod
    def from_dict(cls, component_dict: Dict) -> "ModuleBase":
        _component_dict = deepcopy(component_dict)
        type = _component_dict.pop("type")
        params = _component_dict
        return cls(type, params)

    def update_func(self, module_map):
        self.func = get_support_modules(self.type, module_map)
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")

    def get_params(self, attr):
        return self.params[attr] if attr in self.params else None

    def get_status(self):
        return self.is_active

    def get_value(self, attr):
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")
        else:
            return getattr(self.func, attr, None)

    def set_value(self, attr, value):
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")
        else:
            setattr(self.func, attr, value)


@dataclass
class Module(ModuleBase):
    type: str
    params: Dict[str, Any]
    func: Optional[Callable]

    def __init__(self, type, params):
        super().__init__(type, params)


@dataclass
class Node(ModuleBase):
    type: str
    params: Dict[str, Any]
    modules: Dict[str, Module]
    func: Optional[Callable]

    def __init__(self, type, params, modules):
        super().__init__(type, params)
        self.modules = modules

    @classmethod
    def from_dict(cls, node_dict: Dict) -> "Node":
        _node_dict = deepcopy(node_dict)
        type = _node_dict.pop("type")
        modules_dict = _node_dict.pop("modules")
        modules = {key: Module.from_dict(value) for key, value in modules_dict.items()}
        params = _node_dict
        return cls(type, params, modules)

    def get_params(self, attr):
        if attr in self.params:
            return self.params[attr]
        # Make sure attr ends with "type" when tuning node's modules
        elif attr.endswith("type"):
            return list(self.modules.keys())
        else:
            return None

    def set_value(self, attr, value):
        if self.func is None:
            print(f"{self.__class__.__name__} type {self.type} is not supported.")
        else:
            setattr(self.func, attr, value)
            if value in self.modules:
                module = self.modules[value]
                for param in module.params:
                    val = module.get_params(param)
                    if val:
                        module.set_value(param, val)


class Adaptor:

    def __init__(self, yaml_data: str):
        self.nodes = self.parse_nodes(yaml_data)
        self.root_func: Optional[Callable] = None

        self.rag_pipeline: Optional[RAGPipeline] = None

    def parse_nodes(self, yaml_data):
        parsed_nodes = {}
        for node in yaml_data.get("nodes", []):
            node_type = node.get("node")
            modules_dict = {
                mod.get("module_type"): Module(
                    type=mod.get("module_type", ""),
                    params={k: convert_tuple(v) for k, v in mod.items() if k not in ["module_type"]},
                )
                for mod in node.get("modules", [])
                if mod.get("module_type")
            }
            node_params = {k: convert_tuple(v) for k, v in node.items() if k not in ["node", "node_type", "modules"]}
            cur_node = Node(type=node_type, params=node_params, modules=modules_dict)
            if node_type in parsed_nodes:
                parsed_nodes[node_type].append(cur_node)
            else:
                parsed_nodes[node_type] = [cur_node]
        return parsed_nodes

    def get_node(self, node_type, idx=0):
        nodes = self.nodes[node_type] if node_type in self.nodes else None
        return nodes[idx] if nodes and idx < len(nodes) else None

    def get_modules_from_node(self, node_type, idx=0):
        node = self.get_node(node_type, idx)
        return node.modules if node else None

    def get_module(self, node_type, module_type, idx=0):
        if module_type is None:
            return self.get_node(node_type, idx)
        else:
            modules = self.get_modules_from_node(node_type, idx)
            return modules[module_type] if modules and module_type in modules else None

    def update_all_module_functions_tmp(self, rag_pipeline, node_type_map=COMP_TYPE_MAP):
        module_map = get_ecrag_module_map(rag_pipeline.pl)
        self.root_func = get_support_modules("root", module_map)

        for node_list in self.nodes.values():
            for node in node_list:
                node.update_func(module_map)
                node.is_active = False
                for module in node.modules.values():
                    module.update_func(module_map)
                    module.is_active = False

        self.activate_modules_based_on_type(node_type_map)

    def update_all_module_functions(self, rag_pipeline, node_type_map=COMP_TYPE_MAP):
        self.update_all_module_functions_tmp(rag_pipeline, node_type_map)
        self.rag_pipeline = rag_pipeline

    def activate_modules_based_on_type(self, node_type_map):
        if not self.root_func:
            return

        for node_list in self.nodes.values():
            for node in node_list:
                node_type = node.type
                if not getattr(self.root_func, node_type, None):
                    continue
                node.is_active = True
                active_module_type = getattr(node.func, node_type_map[node_type], None)
                if active_module_type and active_module_type in node.modules:
                    node.modules[active_module_type].is_active = True

    def get_rag_pipelines_candidates(self, params_candidates):
        rag_pls = []
        for params_candidate in params_candidates:
            rag_pl = self.rag_pipeline.copy()
            self.update_all_module_functions_tmp(rag_pl)
            for attr, tunerUpdate in params_candidate.items():
                module = self.get_module(tunerUpdate.node_type, tunerUpdate.module_type)
                module.set_value(attr, tunerUpdate.val)
            rag_pl.regenerate_id()
            rag_pls.append(rag_pl)
        self.update_all_module_functions(self.rag_pipeline)
        return rag_pls, params_candidates
