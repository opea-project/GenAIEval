# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Factualness:
    name = "factualness"
    required_columns = ["answer", "context"]
    template = """- Factualness: Factualness assesses how much of the provided answer is contained within the provided context. A higher score indicates that a higher proportion of claims present in the answer are present or can be derived from the provided context.
  - Score 1: the answer is completely hallucinated i.e. not contained in the context at all or there is no answer.
  - Score 2: only a small part of the answer is contained in the context but most of it is imaginary/hallucinated or the meaning is completely changed from what is represented in the context.
  - Score 3: Only about half of the answer is contained in the context. Rest of the answer is hallucinated or imaginary.
  - Score 4: Most of the claims in the answer can be inferred from the provided context with very little information that is not directly supported by the provided context.
  - Score 5: All of the claims in the answer are directly supported by the provided context, demonstrating high faithfulness to the provided context."""
