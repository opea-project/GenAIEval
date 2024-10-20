#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

from evals.metrics.answer_relevancy import AnswerRelevancyMetric


class TestAnswerRelevancyMetric(unittest.TestCase):

    @unittest.skip("need pass localhost id")
    def test_relevancy(self):
        # Replace this with the actual output from your LLM application
        actual_output = "We offer a 30-day full refund at no extra cost."

        metric = AnswerRelevancyMetric(threshold=0.5, model="http://localhost:8008/generate")
        test_case = {
            "input": "What if these shoes don't fit?",
            "actual_output": actual_output,
        }

        score = metric.measure_zh(test_case)
        print(score)

    @unittest.skip("need pass localhost id")
    def test_deepeval(self):
        from evals.evaluation.deepeval.models.endpoint_models import TGIEndpointModel

        endpoint = TGIEndpointModel(model="http://localhost:8008/generate")

        import os

        # the option of opting out of the telemetry data collection through an environment variable
        # https://github.com/confident-ai/deepeval/blob/main/docs/docs/data-privacy.mdx#your-privacy-using-deepeval
        os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"

        # Replace this with the actual output from your LLM application
        actual_output = "We offer a 30-day full refund at no extra cost."

        from deepeval.metrics import AnswerRelevancyMetric
        from deepeval.test_case import LLMTestCase

        test_case = LLMTestCase(input="What if these shoes don't fit?", actual_output=actual_output)

        metric = AnswerRelevancyMetric(threshold=0.5, model=endpoint, async_mode=False)
        metric.measure(test_case)
        print(metric.score)
        print(metric.reason)

        # test async_mode
        metric = AnswerRelevancyMetric(threshold=0.5, model=endpoint, async_mode=True)
        metric.measure(test_case)
        print(metric.score)
        print(metric.reason)


if __name__ == "__main__":
    unittest.main()
