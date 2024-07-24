#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from evals.metrics.retrieval import RetrievalBaseMetric


class TestRetrievalMetric(unittest.TestCase):

    def test_retrieval(self):

        # Replace this with the expected output from your RAG generator
        golden_context = "You are eligible for a 30 day full refund at no extra cost."

        # Replace this with the actual retrieved context from your RAG pipeline
        retrieval_context = [
            "All customers are eligible for a 30 day full refund at no extra cost.",
            "You are eligible for a 30 day full refund at no extra cost.",
            "We offer a 30-day full refund at no extra cost.",
        ]

        metric = RetrievalBaseMetric()
        test_case = {
            "input": "What if these shoes don't fit?",
            "golden_context": golden_context,
            "retrieval_context": retrieval_context,
        }

        print(metric.measure(test_case))


if __name__ == "__main__":
    unittest.main()
