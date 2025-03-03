# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ast
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple


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
