# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Relevance:
    name = "relevance"
    required_columns = ["question", "answer"]
    template = """- Relevance: Relevance measures how well the answer relates to the question.
  - Score 1: The answer doesn't mention anything about the question or is completely irrelevant to the question.
  - Score 2: The answer only identifies the domain (e.g. cnvrg) mentioned in the question and provides information from the correct domain. But, the answer does not address the question itself and the point of the question is completely missed by it.
  - Score 3: The answer correctly identifies the domain and essence of the question but the details in the answer are not relevant to the focus of the question.
  - Score 4: The answer correctly identifies domain mentioned the question and essence of the question as well as stays consistent with both of them. But there is some part of the answer that is not relevant to the question or it's topic or it's essence. This irrelevant part is damaging the overall relevance of the answer.
  - Score 5: The answer is completely relevant to the question and the details do not deviate from the essence of the question. There are no parts of the answer that are irrelevant or unnecessary for the given question."""
