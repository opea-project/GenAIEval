# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from itertools import product
from typing import Dict, Optional

from components.tuner.base import (
    ContentType,
    Feedback,
    Question,
    Suggestion,
    SuggestionType,
    Target
)
from components.tuner.adaptor import Adaptor


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


def display_ragqna(ragqna):
    print("\nRAG Query\n" "---------\n" f"{ragqna.query}\n\n" "RAG Response\n" "------------\n" f"{ragqna.response}\n")

    if ragqna.contexts:
        for index, context in enumerate(ragqna.contexts):
            cleaned_context = context.replace("\n", " ")
            print(f"RAG Context {index}\n" "-------------------\n" f"{cleaned_context}\n")
    else:
        print("RAG Contexts\n" "------------\n" "None\n")


def display_list(list):
    for index, value in enumerate(list):
        print(f"{index}: {value}")


class Tuner(ABC):

    def __init__(self, question: Question, adaptor: Adaptor, targets: Dict[str, Target]):
        self.question = question

        self.adaptor = adaptor
        self.targets = targets
        

    def check_active(self):
        for target in self.targets.values():
            target_obj = self.adaptor.get_module(target.node_type, target.module_type)
            if not target_obj.get_status():
                return False
        return True

    def set_param(
        self,
        param_name,
        suggestion_type: SuggestionType,
        new_vals: Optional[int] = None,
        step: Optional[int] = None,
        lower_limit: Optional[int] = None,
        count: Optional[int] = 1
    ):
        target_obj = None
        if param_name in self.targets:
            target = self.targets[param_name]
            target_obj = self.adaptor.get_module(target.node_type, target.module_type)

        if not target_obj:
            print(f"[!] Target not found: node={target.node_type}, module={target.module_type}")
            return

        if not target_obj.get_status():
            print(f"[!] Skipping inactive component: node={target.node_type}, module={target.module_type}")
            return

        target.orig_val = target_obj.get_value(target.attribute)

        match suggestion_type:
            case SuggestionType.STEPWISE_GROUPED | SuggestionType.GRID_SEARCH | SuggestionType.STEPWISE:
                if new_vals:
                    target.new_vals = new_vals
                else:
                    if step is None:
                        raise ValueError("Step must be provided for stepwise tuning.")
                    if lower_limit:
                        start = lower_limit
                    else:
                        start = target.orig_val

                    if count:
                        target.new_vals = [start + i * step for i in range(count)]
                    else:
                        target.new_vals = [start + step]

                target.suggestion = Suggestion(
                    hint=f"{target.attribute}'s current value: {target.orig_val}\n"
                        f"Setting it to {target.new_vals}",
                    suggestion_type=suggestion_type
                )
            case SuggestionType.CHOOSE:
                target.new_vals = target_obj.get_params(target.attribute)
                target.suggestion = Suggestion(
                    hint=f"{target.attribute}'s current value: {target.orig_val}\n"
                        f"Please choose a new value from below:",
                    options=target.new_vals,
                    suggestion_type=suggestion_type
                )
            case SuggestionType.ITERATE:
                target.new_vals = target_obj.get_params(target.attribute)
                target.suggestion = Suggestion(
                    hint=f"{target.attribute}'s current value: {target.orig_val}\n"
                        f"Iterate from available values",
                    options=target.new_vals,
                    suggestion_type=suggestion_type
                )
            case SuggestionType.SET:
                if new_vals:
                    target.new_vals = new_vals
                    hint = f"Change {target.attribute}'s value: {target.orig_val} -> {new_vals}\n"
                else:
                    target.new_vals = None
                    hint = f"{target.attribute}'s current value: {target.orig_val}\nPlease enter a new value: "

                target.suggestion = Suggestion(
                    hint=hint,
                    options=target.new_vals,
                    suggestion_type=suggestion_type
                )

    def request_feedback(self):
        if not self.check_active():
            return False

        print(f"\033[1m\033[93m{self}\033[0m: {self.question}\n")
        valid, user_input = input_parser(len(self.question.options))
        if not valid:
            return False

        self.user_feedback = Feedback(feedback=user_input)
        return self._feedback_to_suggestions()

    @abstractmethod
    def _feedback_to_suggestions(self):
        pass

    def apply_suggestions(self):
        if not self.check_active():
            return

        params_candidates = []

        new_values_dict = {}
        
        # STEPWISE_GROUPED
        grouped_targets = {
            a: t for a, t in self.targets.items()
            if t.suggestion and t.suggestion.suggestion_type == SuggestionType.STEPWISE_GROUPED
        }
        if grouped_targets:
            count = min(len(t.new_vals) for t in grouped_targets.values())

            for idx in range(count):
                candidate = {a: t.new_vals[idx] for a, t in grouped_targets.items()}
                new_values_dict = {
                    a: [(t.node_type, t.module_type), t.new_vals[idx]]
                    for a, t in grouped_targets.items()
                }
                params_candidates.append(new_values_dict)
            if len(params_candidates) > 0:
                return self.adaptor.get_rag_pipelines_candidates(params_candidates) 

        # GRID_SEARCH
        from itertools import product
        grid_targets = {
            a: t for a, t in self.targets.items()
            if t.suggestion and t.suggestion.suggestion_type == SuggestionType.GRID_SEARCH
        }
        if grid_targets:
            keys, values_list = zip(*((a, t.new_vals) for a, t in grid_targets.items()))
            for combination in product(*values_list):
                candidate = dict(zip(keys, combination))
                new_values_dict = {}
                for a, val in candidate.items():
                    new_values_dict[a] = [(self.targets[a].node_type, self.targets[a].module_type), val]
                params_candidates.append(new_values_dict)
            if len(params_candidates) > 0:
                return self.adaptor.get_rag_pipelines_candidates(params_candidates)

        new_values_dict = {}
        for attr, target in self.targets.items():
            suggestion = target.suggestion
            if not suggestion or attr in new_values_dict:
                continue

            orig_val = target.orig_val
            match suggestion.suggestion_type:
                case SuggestionType.SET:
                    print(f"{suggestion}")
                    if suggestion.options:
                        new_values_dict[attr] = [(target.node_type, target.module_type), suggestion.options[0].content]
                    else:
                        valid, user_input = input_parser()
                        if valid:
                            new_values_dict[attr] = [(target.node_type, target.module_type), user_input]

                case SuggestionType.CHOOSE:
                    print(f"{suggestion}")
                    new_options = [x for x in suggestion.options if x != orig_val]
                    valid, user_input = input_parser(len(new_options))
                    if valid:
                        chosed_val = suggestion.options[user_input-1]
                        new_values_dict[attr] = [(target.node_type, target.module_type), chosed_val.content]

                case SuggestionType.ITERATE:
                    print(f"{suggestion}")
                    for option in suggestion.options:
                        new_values_dict = {}
                        new_values_dict[attr] = [(target.node_type, target.module_type), option.content]
                        params_candidates.append(new_values_dict)
                    if len(params_candidates) > 0:
                        return self.adaptor.get_rag_pipelines_candidates(params_candidates)

                case SuggestionType.STEPWISE:
                    if len(target.new_vals) == 1:
                        val = target.new_vals[idx]
                        new_values_dict[attr] = [(target.node_type, target.module_type), val]
                    else:
                        for idx in range(len(target.new_vals)):
                            new_values_dict = {}
                            val = target.new_vals[idx]
                            new_values_dict[attr] = [(target.node_type, target.module_type), val]
                            params_candidates.append(new_values_dict)
                        if len(params_candidates) > 0:
                            return self.adaptor.get_rag_pipelines_candidates(params_candidates)

                case _:
                    print(f"ERROR: Unknown suggestion type '{suggestion.suggestion_type}'.")

        params_candidates.append(new_values_dict)
        return self.adaptor.get_rag_pipelines_candidates(params_candidates)

    def __str__(self):
        return f"{self.__class__.__name__}"


class EmbeddingTuner(Tuner):
    def __init__(self, adaptor: Adaptor):
        # question
        question = Question(
            hint="Do you want to tune embedding model",
            options=["Yes, iterate it from available options", 
                    "No, skip this tuner"],
        )

        targets = {}
        # targets
        attribute="embedding_model"
        target = Target(
            node_type="indexer",
            attribute=attribute,
        )
        targets[attribute] = target

        super().__init__(question, adaptor, targets)


    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if self.user_feedback.feedback == 1:
            self.set_param(
                param_name="embedding_model", 
                suggestion_type=SuggestionType.ITERATE)
            return True
        else:
            return False


class NodeParserTuner(Tuner):

    def __init__(self, adaptor: Adaptor):
        # question
        question = Question(
            hint="Do you want to tune node parser",
            options=["Yes, iterate it from available options", 
                    "No, skip this tuner"],
        )
        
        targets = {}
        # targets
        attribute="parser_type"
        target = Target(
            node_type="node_parser",
            attribute=attribute,
        )
        targets[attribute] = target

        super().__init__(question, adaptor, targets)

    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if self.user_feedback.feedback == 1:
            self.set_param(
                param_name="parser_type", 
                suggestion_type=SuggestionType.ITERATE)
            return True
        else:
            return False


class SimpleNodeParserChunkTuner(Tuner):

    def __init__(self, adaptor: Adaptor):
        # question
        question = Question(
            hint="Do you want to tune chunk size and chunk overlap",
            options=["Yes, iterate the chunk size and chunk overlap based on current values stepwisely",
                    "Yes, set them to designated values",
                    "No, skip this tuner"],
        )
        
        targets = {}
        # targets
        attribute="chunk_size"
        target = Target(
            node_type="node_parser",
            module_type="simple",
            attribute=attribute,
        )
        targets[attribute] = target

        attribute="chunk_overlap"
        target = Target(
            node_type="node_parser",
            module_type="simple",
            attribute=attribute,
        )
        targets[attribute] = target

        super().__init__(question, adaptor, targets)

    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if self.user_feedback.feedback == 1:
            self.set_param(
                param_name="chunk_size", 
                suggestion_type=SuggestionType.STEPWISE_GROUPED, 
                step=100,
                count=3)
            self.set_param(
                param_name="chunk_overlap", 
                suggestion_type=SuggestionType.STEPWISE_GROUPED, 
                step=16,
                count=3)
            return True
        elif self.user_feedback.feedback == 2:
            self.set_param(
                param_name="chunk_size", 
                suggestion_type=SuggestionType.SET)
            self.set_param(
                param_name="chunk_overlap", 
                suggestion_type=SuggestionType.SET)
            return True
        else:
            return False


class RetrievalTopkTuner(Tuner):

    def __init__(self, adaptor: Adaptor):
        # question
        question = Question(
            hint="Do you want to tune retrieve's topk",
            options=["Yes, iterate it based on current values stepwisely", 
                     "Yes, set it to designated value",
                    "No, skip this tuner"],
        )

        targets = {}
        # targets
        attribute="retrieve_topk"
        target = Target(
            node_type="retriever",
            attribute=attribute,
        )
        targets[attribute] = target

        super().__init__(question, adaptor, targets)


    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if self.user_feedback.feedback == 1:
            self.set_param(
                param_name="retrieve_topk", 
                suggestion_type=SuggestionType.STEPWISE, 
                step=15,
                lower_limit=30,
                count=4
                )
            return True
        if self.user_feedback.feedback == 2:
            self.set_param(
                param_name="retrieve_topk", 
                suggestion_type=SuggestionType.SET, 
                )
            return True
        else:
            return False


class RerankerTopnTuner(Tuner):

    def __init__(self, adaptor: Adaptor):
        # question
        question = Question(
            hint="Do you want to tune reranker's top_n",
            options=["Yes, iterate it based on current values stepwisely", 
                    "No, skip this tuner"],
        )

        targets = {}
        # targets
        attribute="top_n"
        target = Target(
            node_type="postprocessor",
            module_type="reranker",
            attribute=attribute,
        )
        targets[attribute] = target

        super().__init__(question, adaptor, targets)


    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if self.user_feedback.feedback == 1:
            self.set_param(
                param_name="top_n", 
                suggestion_type=SuggestionType.STEPWISE, 
                step=5,
                lower_limit=5,
                count=2
                )
            return True
        else:
            return False


class RetrievalTopkRerankerTopnTuner(Tuner):

    def __init__(self, adaptor: Adaptor):
        # question
        question = Question(
            hint="Do you want to tune retrieve_topk and reranker's top_n",
            options=["Yes, iterate it based on current values stepwisely", 
                     "Yes, set retrieve_topk to [30, 50, 100, 200], top_n to [5, 10]", 
                    "No, skip this tuner"],
        )

        targets = {}
        # targets
        attribute="retrieve_topk"
        target = Target(
            node_type="retriever",
            attribute=attribute,
        )
        targets[attribute] = target

        attribute="top_n"
        target = Target(
            node_type="postprocessor",
            module_type="reranker",
            attribute=attribute,
        )
        targets[attribute] = target

        super().__init__(question, adaptor, targets)


    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if self.user_feedback.feedback == 1:
            self.set_param(
                param_name="retrieve_topk", 
                suggestion_type=SuggestionType.GRID_SEARCH, 
                step=15,
                lower_limit=30,
                count=4
                )
            self.set_param(
                param_name="top_n", 
                suggestion_type=SuggestionType.GRID_SEARCH, 
                step=5,
                lower_limit=5,
                count=2
                )
            return True
        if self.user_feedback.feedback == 2:
            self.set_param(
                param_name="retrieve_topk", 
                suggestion_type=SuggestionType.GRID_SEARCH, 
                new_vals=[30, 50, 100, 200]
                )
            self.set_param(
                param_name="top_n", 
                suggestion_type=SuggestionType.GRID_SEARCH, 
                step=5,
                lower_limit=5,
                count=2
                )
            return True
        else:
            return False
