# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import Enum, auto
from typing import List, Optional, Union

from pydantic import BaseModel, validator
from api_schema import RunningStatus
from components.pilot.base import Node, Module, Attribute
from components.pilot.pipeline import Pipeline
from api_schema import TunerUpdateOut

from collections import defaultdict
import itertools
import copy


class ContentType(Enum):
    ALL_CONTEXTS = auto()
    CONTEXT = auto()
    RESPONSE = auto()


class OptionItem(BaseModel):
    idx: int
    content: str

    def __str__(self):
        return f"{self.idx}: {self.content}"


class UserInput(BaseModel):
    hint: str
    options: Optional[List[OptionItem]] = None

    @validator("options", pre=True)
    def auto_generate_ids(cls, v):
        if v is None:
            return v
        if all(isinstance(item, str) for item in v):
            return [{"idx": idx, "content": item} for idx, item in enumerate(v, start=1)]
        return v

    def __str__(self):
        options_str = ""
        if self.options:
            options_str = "\n" + "\n".join(str(option) for option in self.options)
        return f"{self.hint}{options_str}"


class Question(UserInput):
    status: Optional[str] = None

    def __str__(self):
        status_str = f"{self.status}\n" if self.status else ""
        options_str = ""
        if self.options:
            options_str = "\n" + "\n".join(str(option) for option in self.options)
        return f"{status_str}{self.hint}{options_str}"


class SuggestionType(Enum):
    CHOOSE = auto()
    ITERATE = auto()
    SET = auto()
    STEPWISE_GROUPED = auto()
    STEPWISE = auto()
    GRID_SEARCH = auto()
    NONE = auto()


class Suggestion(UserInput):
    suggestion_type: SuggestionType


class Feedback(BaseModel):
    feedback: bool | int
    auto: bool


class DirectionType(Enum):
    INCREASE = auto()
    DECREASE = auto()


class Target(BaseModel):
    node_type: str
    module_type: str
    attribute_type: str
    orig_val: Optional[Union[int, float, str]] = None
    new_vals: List[Union[int, float, str]] = None
    suggestion: Suggestion = None

    def as_string(self) -> str:
        module = f"{self.module_type}." if self.module_type else ""
        return f"{self.node_type}.{module}{self.attribute_type}"


class TargetUpdate(BaseModel):
    node_type: str
    module_type: Optional[str] = None
    attribute: str
    val: Optional[Union[int, float, str]] = None


def input_parser(upper_limit: int = None):
    if upper_limit:
        user_input = input(f"(1 - {upper_limit}): ")
    else:
        user_input = input("Provide a number: ")
        upper_limit = 10000

    if user_input.isdigit() and 1 <= int(user_input) <= upper_limit:
        return True, int(user_input)
    else:
        print(f"Invalid input. Please enter a number between 1 and {upper_limit}.")
        return False, None


class Tuner:

    name: str

    def __init__(self, tuner_dict: dict):
        if tuner_dict["params"]["name"]:
            self.name = tuner_dict["params"]["name"]
        else:
            self.name = tuner_dict["type"]
        self.node = Node.from_dict(tuner_dict)
        targets = {}
        for m in self.node.modules:
            for attr in m.attributes:
                target = Target(
                    node_type=self.node.type,
                    module_type=m.type,
                    attribute_type=attr.type,
                    new_vals=attr.params["values"],
                )
                targets[attr.type] = target

        # A target aims for an attribute
        # The key of targets dict is the attribute type
        self.targets = targets
        self._status = RunningStatus.NOT_STARTED
        self.tunerUpdateOuts = []

    def set_status(self, status: RunningStatus):
        self._status = status

    def get_status(self):
        return self._status

    def set_status_completed(self):
        self._status = RunningStatus.COMPLETED

    def reset(self):
        self._status = RunningStatus.NOT_STARTED
        self.tunerUpdateOuts = []

    # Convert targets to pipeline candidate
    def run(self, pl_template):
        attribute_candidates = []
        for k, tgt in self.targets.items():
            tgt_node = get_node_from_pipeline(pl_template, tgt.node_type)
            if tgt_node:
                tgt_module = get_module_from_node(tgt_node, tgt.module_type)
                if tgt_module:
                    tgt_attr = get_attr_from_module(tgt_module, tgt.attribute_type)
                    if tgt_attr:
                        for v in tgt.new_vals:
                            attribute_candidates.append((tgt_node.type, tgt_module.type, tgt_attr.type, v))
                    else:
                        print(f"Tuner attribute {tgt.attribute_type} is not applicable to the pipeline")
                        continue

                else:
                    print(f"Tuner module {tgt.module_type} is not applicable to the pipeline")
                    continue

            else:
                print(f"Tuner node {tgt.node_type} is not applicable to the pipeline")
                continue
        if len(attribute_candidates) == 0:
            return []

        print(attribute_candidates)
        node_suggestions = generate_node_suggestion(attribute_candidates)
        print(node_suggestions)
        suggestion_list = []
        # Single node pipeline
        # TODO: Could extend to a pipeline suggestion
        for n in node_suggestions:
            # Reconstruct pipelines for a tuner
            tgt_pl = copy.deepcopy(pl_template)
            tgt_pl.regenerate_id()
            for n_to_del in tgt_pl.nodes:
                if n_to_del.type == n.type:
                    tgt_pl.nodes.remove(n_to_del)
            tgt_pl.nodes.append(n)
            suggestion_list.append(tgt_pl)

            # Generate TunerUpdateOuts
            targets = {}
            for module in n.modules:
                for attr in module.attributes:
                    parts = [n.type, module.type, attr.type]
                    target_key = ".".join(parts)  # e.g., "postprocessor.reranker.top_n"
                    targets[target_key] = attr.params["value"]
            self.tunerUpdateOuts.append(
                TunerUpdateOut(
                    tuner_name=self.name,
                    base_pipeline_id=pl_template.id,
                    pipeline_id=tgt_pl.id,
                    targets=targets,
                )
            )
        return suggestion_list


# attr_candidate = (node_type, module_type, attribute_type, attr_value)
# attributes will be expanded
def generate_node_suggestion(attr_candidates: []):
    grouped = defaultdict(list)
    for n, m, a, v in attr_candidates:
        grouped[(n, m, a)].append(v)

    # group by (n, m) → map attribute type → values
    nm_grouped = defaultdict(lambda: defaultdict(list))
    for (n, m, a), v_list in grouped.items():
        nm_grouped[(n, m)][a] = v_list

    results = []
    for (n, m), a_to_vs in nm_grouped.items():
        # Build cartesian product of choices for each attribute type
        choice_lists = [[Attribute(type=a, params={"value": v}) for v in vs] for a, vs in a_to_vs.items()]

        for combo in itertools.product(*choice_lists):
            module = Module(type=m, attributes=list(combo))
            node = Node(type=n, modules=[module])
            results.append(node)
    return results


# TODO: Move to Node impelmentation
def get_node_from_pipeline(pl: Pipeline, node_type: str):
    for n in pl.nodes:
        if n.type == node_type:
            return n
    return None


def get_module_from_node(node: Node, module_type: str):
    for m in node.modules:
        if m.type == module_type:
            return m
    return None


def get_attr_from_module(mod: Module, attribute_type: str):
    for a in mod.attributes:
        if a.type == attribute_type:
            return a
    return None
