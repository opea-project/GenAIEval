# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class ContextRelevance:
    name = "context_relevance"
    required_columns = ["question", "context"]
    template = """- Context Relevance: Context Relevance measures how well the context relates to the question.
  - Score 1: The context doesn't mention anything about the question or is completely irrelevant to the question.
  - Score 2: The context only identifies the domain (e.g. cnvrg) mentioned in the question and provides information from the correct domain. But, the context does not address the question itself and the point of the question is completely missed by it.
  - Score 3: The context correctly identifies the domain and essence of the question but the details in the context are not relevant to the focus of the question.
  - Score 4: The context correctly identifies domain mentioned the question and essence of the question as well as stays consistent with both of them. But there is some part of the context that is not relevant to the question or it's topic or it's essence. This irrelevant part is damaging the overall relevance of the context.
  - Score 5: The context is completely relevant to the question and the details do not deviate from the essence of the question. There are no parts of the context that are irrelevant or unnecessary for the given question."""
