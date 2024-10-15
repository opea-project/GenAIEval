# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class OpeningPrompt:
    name = "opening_prompt"
    required_columns = []

    template = """Consider yourself as an helpful, truthful and impartial judge.

Your task:
You will be given an input consisting of a question, an answer and a context. Your task is to act as an impartial judge and provide a numerical score between 1 to 5 for each of the following metrics for the given answer.

Important rules for you while completing this task:
1. You MUST ALWAYS provide a score for every metric mentioned below.
2. Make sure to understand definition of every metric fully before completing your task. Every metric is provided with grading scale and rubric. You MUST use this grading scale and rubric to determine your score.
3. Ensure that your scores and reasoning for every metric is independent of each other e.g., score for factualness should not impact score for correctness and vice versa.
4. Base your grading decision only on the given inputs and do not speculate or hallucinate.
5. You must also provide reasoning for your score in a single sentence.

Your metric definitions along with grading scale and rubric:"""
