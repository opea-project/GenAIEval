#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import unittest

from evals.metrics.ragaaf import AnnotationFreeEvaluate

host_ip = os.getenv("host_ip", "localhost")
port = os.getenv("port", "8008")


class TestRagaafMetric(unittest.TestCase):

    @unittest.skip("need pass localhost id")
    def test_ragaaf(self):

        dataset = "sample data"
        data_mode = "unit"
        field_map = {"question": "question", "answer": "actual_output", "context": "contexts"}

        question = "What if these shoes don't fit?"
        actual_output = "We offer a 30-day full refund at no extra cost."
        contexts = [
            "All customers are eligible for a 30 day full refund at no extra cost.",
            "We can only process full refund upto 30 day after the purchase.",
        ]
        examples = [{"question": question, "actual_output": actual_output, "contexts": contexts}]

        evaluation_mode = "endpoint"
        model_name = f"http://{host_ip}:{port}"

        evaluation_metrics = ["factualness", "relevance", "correctness", "readability"]

        evaluator = AnnotationFreeEvaluate(
            dataset=dataset,
            data_mode=data_mode,
            field_map=field_map,
            evaluation_mode=evaluation_mode,
            model_name=model_name,
            evaluation_metrics=evaluation_metrics,
            examples=examples,
            debug_mode=True,
        )

        responses = evaluator.measure()

        for response in responses:
            print(response)


if __name__ == "__main__":
    unittest.main()
