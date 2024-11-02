# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class ContextRecall:
    name = "context_recall"
    required_columns = ["context", "ground_truth"]
    template = """- Context Recall: context recall measures how well ground truth is supported by the context.
  - Score 1: None of facts/steps/aspects in the ground truth are supported by the context.
  - Score 2: Only a small part of facts/steps/aspects in the ground truth are supported by the context.
  - Score 3: About half of facts/steps/aspects in the ground truth are supported by the context.
  - Score 4: All main/important facts/steps/aspects in the ground truth are supported by the context but some of the details are not supported by the context.
  - Score 5: All of facts/steps/aspects in the ground truth are supported by the context. """
