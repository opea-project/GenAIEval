#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
import unittest

from evals.metrics.auto_eval import AutoEvaluate

host_ip = os.getenv("host_ip", "localhost")
port = os.getenv("port", "8008")


class TestRagasMetric(unittest.TestCase):

    # @unittest.skip("need pass localhost id")
    def test_ragas(self):

        dataset = "explodinggradients/ragas-wikiqa"
        data_mode = "benchmarking"
        field_map = {"question": "question", "answer": "generated_with_rag", "context": "context"}

        evaluation_mode = "endpoint"
        model_name = f"http://{host_ip}:{port}"

        evaluation_metrics = ["factualness", "relevance", "correctness", "readability"]

        evaluator = AutoEvaluate(
            dataset=dataset,
            data_mode=data_mode,
            field_map=field_map,
            evaluation_mode=evaluation_mode,
            model_name=model_name,
            evaluation_metrics=evaluation_metrics,
            debug_mode=True,
        )

        responses = evaluator.measure()

        for response in responses:
            print(response)


if __name__ == "__main__":
    unittest.main()
