# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class Correctness:
    name = "correctness"
    required_columns = ["answer", "context", "question"]
    template = """- Correctness: correctness measures how accurately and comprehensively does the answer resolve problem posed in the question.
  - Score 1: If the answer is empty string or something like "I do not know the answer", the correctness score is 1.
  - Score 2: If the answer only addresses a small part of the question correctly or it is missing many critical steps/aspects of the answer or the answer is too short to fully answer the question or is missing many steps causing the answer to not fully address the problem described in the question, then the correctness score is 2.
  - Score 3: The answer mostly addresses the question but one critical aspect/step is missing or is incorrect.
  - Score 4: the answer mostly answer the question and covers all critical/main aspects of the question, but it’s missing important/necessary details about one or more aspects.
  - Score 5: the answer correctly and completely addresses the query. It also covers important details about each step."""
