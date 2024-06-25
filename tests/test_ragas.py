#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#
import unittest

from evals.metrics.ragas import RagasMetric


@unittest.skip("need assign localhost id")
class TestRagasMetric(unittest.TestCase):
    # Replace this with the actual output from your LLM application
    actual_output = "We offer a 30-day full refund at no extra cost."

    # Replace this with the expected output from your RAG generator
    expected_output = "You are eligible for a 30 day full refund at no extra cost."

    # Replace this with the actual retrieved context from your RAG pipeline
    retrieval_context = ["All customers are eligible for a 30 day full refund at no extra cost."]

    metric = RagasMetric(threshold=0.5, model="http://10.45.76.150:8008")
    test_case = {
        "input": "What if these shoes don't fit?",
        "actual_output": actual_output,
        "expected_output": expected_output,
        "retrieval_context": retrieval_context,
    }

    metric.measure(test_case)
    print(metric.score)


if __name__ == "__main__":
    unittest.main()
