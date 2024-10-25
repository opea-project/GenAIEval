#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from evals.metrics.hallucination import HallucinationMetric


class TestHallucinationMetric(unittest.TestCase):

    @unittest.skip("need pass localhost id")
    def test_hallucination(self):
        # Replace this with the actual output from your LLM application
        actual_output = "A blond drinking water in public."

        # Replace this with the actual documents that you are passing as input to your LLM.
        context = ["A man with blond-hair, and a brown shirt drinking out of a public water fountain."]

        # metric = HallucinationMetric(threshold=0.5, model="http://localhost:8008/generate")
        metric = HallucinationMetric(threshold=0.5, model="http://localhost:8008")
        test_case = {"input": "What was the blond doing?", "actual_output": actual_output, "context": context}

        metric.measure(test_case)
        print(metric.score)

    @unittest.skip("need pass localhost id")
    def test_deepeval(self):
        from evals.evaluation.deepeval.models.endpoint_models import TGIEndpointModel

        endpoint = TGIEndpointModel(model="http://localhost:8008/generate")

        import os

        # the option of opting out of the telemetry data collection through an environment variable
        # https://github.com/confident-ai/deepeval/blob/main/docs/docs/data-privacy.mdx#your-privacy-using-deepeval
        os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
        from deepeval.metrics import HallucinationMetric
        from deepeval.test_case import LLMTestCase

        context = ["A man with blond-hair, and a brown shirt drinking out of a public water fountain."]

        actual_output = "A blond drinking water in public."
        test_case = LLMTestCase(input="What was the blond doing?", actual_output=actual_output, context=context)

        metric = HallucinationMetric(threshold=0.5, model=endpoint)
        metric.measure(test_case)
        print(metric.score)
        print(metric.reason)

        # test async_mode
        metric = HallucinationMetric(threshold=0.5, model=endpoint, async_mode=True)
        metric.measure(test_case)
        print(metric.score)
        print(metric.reason)


if __name__ == "__main__":
    unittest.main()
