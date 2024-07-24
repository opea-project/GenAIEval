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


if __name__ == "__main__":
    unittest.main()
