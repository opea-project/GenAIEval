# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod

from components.tuner.base import (
    Question, QuestionType,
    Feedback, ContentType,
    Suggestion, SuggestionType, SuggestionValue, DirectionType,
    RagResult
)


def input_parser(qtype: QuestionType = QuestionType.BOOL):
    user_input = input(f"({qtype.value}): ")

    match qtype:
        case QuestionType.RATING5:
            if user_input.isdigit() and 1 <= int(user_input) <= 5:
                return True, int(user_input)
            else:
                print("Invalid input. Please enter a number between 1 and 5.")
                return False, None

        case QuestionType.RATING3:
            if user_input.isdigit() and 1 <= int(user_input) <= 3:
                return True, int(user_input)
            else:
                print("Invalid input. Please enter a number between 1 and 3.")
                return False, None

        case QuestionType.BOOL:
            if user_input.lower() == "y":
                return True, True
            elif user_input.lower() == "n":
                return True, False
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")
                return False, None

        case QuestionType.SCORE:
            if user_input.isdigit():
                return True, int(user_input)
            else:
                print("Invalid input. Please enter a valid score (integer).")
                return False, None

        case QuestionType.MINUS_ONE_ZERO_ONE:
            if user_input in {"-1", "0", "1"}:
                return True, int(user_input)
            else:
                print("Invalid input. Please enter -1, 0, or 1.")
                return False, None

        case _:
            print("Unknown question type.")
            return False, None


def display_ragqna(ragqna, content_type=ContentType.RESPONSE, context_idx=0):
    print("\nRAG Query\n"
          "---------\n"
          f"{ragqna.query}\n\n"
          "RAG Response\n"
          "------------\n"
          f"{ragqna.response}\n")

    if content_type == ContentType.ALL_CONTEXTS:
        if ragqna.contexts:
            for index, context in enumerate(ragqna.contexts):
                cleaned_context = context.replace('\n', ' ')
                print(f"RAG Context {index}\n"
                      "-------------------\n"
                      f"{cleaned_context}\n")
        else:
            print("RAG Contexts\n"
                  "------------\n"
                  "None\n")
    elif content_type == ContentType.CONTEXT:
        print(f"RAG Contexts {context_idx}\n"
              "--------------------------\n"
              f"{ragqna.contexts[context_idx] if context_idx in ragqna.contexts else 'None'}\n")


def display_list(list):
    for index, value in enumerate(list):
        print(f"{index}: {value}")


class Tuner(ABC):

    def __init__(self,
                 ragqna: RagResult,
                 question: str,
                 question_type: QuestionType,
                 content_type: ContentType):

        self.question = Question(
            question=question,
            question_type=question_type,
            content_type=content_type,
        )
        self.user_feedback: Feedback = None
        self.suggestions: dict[str, Suggestion] = {}

        self.ragqna: RagResult = ragqna

        self.node_type = None
        self.module_type = None
        self.module = None
        self.module_active = False

    def init_ragqna(self, ragqna):
        self.ragqna = ragqna
        self.user_feedback = None
        for suggestion in self.suggestions.values():
            suggestion.reset()

    def update_module(self, module):
        self.module = module
        self.module_active = module.get_status()

    def get_suggestions_origval(self):
        if not self.module_active:
            return
        for suggestion in self.suggestions.values():
            suggestion.origval = self.module.get_value(suggestion.attribute)

    def _display_question(self, content_type, context_idx=0):
        display_ragqna(self.ragqna, content_type, context_idx)
        print(f"{self}: {self.question.question}\n")

    def request_feedback(self):
        if not self.module_active:
            return

        self._display_question(self.question.content_type)

        valid, user_input = input_parser(self.question.question_type)
        if not valid:
            return False

        self.user_feedback = Feedback(
            type=self.question.question_type,
            feedback=user_input
        )
        self.get_suggestions_origval()
        return True

    @abstractmethod
    def _feedback_to_suggestions(self):
        pass

    def make_suggestions(self):
        if not self.module_active:
            return

        self._feedback_to_suggestions()

        old_new_values = {}
        for attr, suggestion in self.suggestions.items():
            svalue = suggestion.svalue
            origval = suggestion.origval

            match svalue.suggestion_type:
                case SuggestionType.SET:
                    choices = suggestion.svalue.choices
                    if not choices:
                        continue

                    print(f"{attr}'s current value: {origval}\n"
                        f"We suggest setting a new value from choices: {choices}\n"
                        f"Please enter a new value: ")
                    valid, user_input = input_parser(QuestionType.SCORE)
                    if valid:
                        old_new_values[attr] = [origval, user_input]

                case SuggestionType.OFFSET:
                    match svalue.direction:
                        case DirectionType.INCREASE:
                            old_new_values[attr] = [origval, origval + svalue.step]
                        case DirectionType.DECREASE:
                            old_new_values[attr] = [origval, origval - svalue.step]
                        case _:
                            print(f"ERROR: Unknown direction '{svalue.direction}' for OFFSET.")

                case SuggestionType.CHOOSE:
                    choices = suggestion.svalue.choices
                    if not choices:
                        continue

                    display_list(choices)
                    print(f"{attr}'s current value: {origval}\n"
                        f"Please enter the index of a new value")
                    valid, user_input = input_parser(QuestionType.SCORE)
                    if valid:
                        if user_input < 0 or user_input >= len(choices):
                            print(f"ERROR: The chosen index {user_input} is out of range")
                        elif origval == choices[user_input]:
                            print(f"ERROR: You chose the current value {user_input}: {choices[user_input]}")
                        else:
                            old_new_values[attr] = [origval, choices[user_input]]

                case _:
                    print(f"ERROR: Unknown suggestion type '{svalue.suggestion_type}'.")

        if not old_new_values:
            return False

        is_changed = False
        for k, v in old_new_values.items():
            if self._confirm_suggestion(self.suggestions[k], v, skip_confirming = True):
                is_changed = True

        if is_changed:
            self._apply_suggestions()

        return is_changed

    def _confirm_suggestion(self, suggestion, old_new_value, skip_confirming=False):
        svalue = suggestion.svalue
        origval, newval = old_new_value

        print(f"Based on your feedback, {svalue.direction.value if svalue.direction else 'modify'} {suggestion.attribute} {origval} -> {newval}")
        if skip_confirming:
            valid, user_input = True, True
        else:
            valid, user_input = input_parser(QuestionType.BOOL)

        if not valid:
            return False

        suggestion.is_accepted = user_input
        if suggestion.is_accepted:
            suggestion.svalue.val = newval
            return True

        return False

    def _apply_suggestions(self):
        for suggestion in self.suggestions.values():
            if suggestion.is_accepted:
                self.module.set_value(suggestion.attribute, suggestion.svalue.val)

    def __str__(self):
        return f"{self.__class__.__name__}"


class SimpleNodeParserChunkTuner(Tuner):

    def __init__(self,
                 ragqna=None):
        q = "Is each context split properly? \n -1) Incomplete \n 0) Good enough or skip currrent tuner \n 1) Includes too many contents"
        super().__init__(ragqna, q, QuestionType.MINUS_ONE_ZERO_ONE, ContentType.ALL_CONTEXTS)

        self.node_type = "node_parser"
        self.module_type = "simple"

        attribute = "chunk_size"
        suggestion = Suggestion(
            svalue=SuggestionValue(
                suggestion_type=SuggestionType.OFFSET,
                step=100),
            attribute=attribute,
        )
        self.suggestions[attribute] = suggestion

        attribute = "chunk_overlap"
        suggestion = Suggestion(
            svalue=SuggestionValue(
                suggestion_type=SuggestionType.OFFSET,
                step=8),
            attribute=attribute,
        )
        self.suggestions[attribute] = suggestion

    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if (self.user_feedback.type == QuestionType.MINUS_ONE_ZERO_ONE):
            if (self.user_feedback.feedback == 1):
                for suggestion in self.suggestions.values():
                    suggestion.svalue.direction = DirectionType.DECREASE
            elif (self.user_feedback.feedback == -1):
                for suggestion in self.suggestions.values():
                    suggestion.svalue.direction = DirectionType.INCREASE


class RerankerTopnTuner(Tuner):

    def __init__(self,
                 ragqna=None):
        q = "Are the contexts not enough for answering the question or some of them contain irrelevant information?\n" + \
            " -1) Not enough \n 0) Fine or skip currrent tuner \n 1) Too many contexts"
        super().__init__(ragqna, q, QuestionType.MINUS_ONE_ZERO_ONE, ContentType.ALL_CONTEXTS)

        self.node_type = "postprocessor"
        self.module_type = "reranker"

        attribute = "top_n"
        suggestion = Suggestion(
            svalue=SuggestionValue(
                suggestion_type=SuggestionType.OFFSET,
                step=1),
            attribute=attribute,
        )
        self.suggestions[attribute] = suggestion

    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if (self.user_feedback.type == QuestionType.MINUS_ONE_ZERO_ONE):
            if (self.user_feedback.feedback == 1):
                for suggestion in self.suggestions.values():
                    suggestion.svalue.direction = DirectionType.DECREASE
            elif (self.user_feedback.feedback == -1):
                for suggestion in self.suggestions.values():
                    suggestion.svalue.direction = DirectionType.INCREASE


class EmbeddingLanguageTuner(Tuner):

    def __init__(self,
                 ragqna=None):
        q = "Does any context contain relevant information for the given RAG query?\n" + \
            " y) yes or skip currrent tuner \n n) no"
        super().__init__(ragqna, q, QuestionType.BOOL, ContentType.ALL_CONTEXTS)

        self.node_type = "indexer"
        self.module_type = None

        attribute = "embedding_model"
        suggestion = Suggestion(
            svalue=SuggestionValue(
                suggestion_type=SuggestionType.CHOOSE,
            ),
            attribute=attribute,
        )
        self.suggestions[attribute] = suggestion

    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if (self.user_feedback.type == QuestionType.BOOL):
            if not self.user_feedback.feedback:
                for suggestion in self.suggestions.values():
                    suggestion.svalue.choices = self.module.get_params(suggestion.attribute)


class NodeParserTypeTuner(Tuner):

    def __init__(self,
                 ragqna=None):
        q = "Are all contexts split with similar amount of information? \n" + \
            "y) All contexts contain similar amount of information or skip currrent tuner \n" + \
            "n) Some contexts contain more information while some contain less"
        super().__init__(ragqna, q, QuestionType.BOOL, ContentType.ALL_CONTEXTS)

        self.node_type = "node_parser"
        self.module_type = None

        attribute = "parser_type"
        suggestion = Suggestion(
            svalue=SuggestionValue(
                suggestion_type=SuggestionType.CHOOSE,
            ),
            attribute=attribute,
        )
        self.suggestions[attribute] = suggestion

    def _feedback_to_suggestions(self):
        assert isinstance(self.user_feedback, Feedback)
        if (self.user_feedback.type == QuestionType.BOOL):
            if not self.user_feedback.feedback:
                for suggestion in self.suggestions.values():
                    suggestion.svalue.choices = self.module.get_params(suggestion.attribute)
