# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Readability:
    name = "readability"
    required_columns = ["answer"]
    template = """- Readability: Readability measures clarity and lucidity of the answer. Readability is measured solely based on the answer and it does not consider the question or the context.
  - Score 1: the answer is empty or "I do not know the answer" or completely unreadable or No meaningful information can be extracted from the answer, then the score is 1.
  - Score 2: the answer is slightly readable, there are irrelevant symbols or HTML tags or repeated words, but it can roughly form a meaningful sentence that can cover some aspects of the answer.
  - Score 3: Answer can be read but there are grammatical mistakes in the answer.
  - Score 4: the answer readable, but the readability and style can improved to better appeal to the reader.
  - Score 5: the answer is reader friendly and well written."""
