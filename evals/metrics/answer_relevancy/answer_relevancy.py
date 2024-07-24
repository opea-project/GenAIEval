#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Dict, Optional, Union

import requests
from requests.exceptions import RequestException

from .template import AnswerRelevancyTemplate


class AnswerRelevancyMetric:
    def __init__(
        self,
        threshold: float = 0.5,
        model: Optional[Union[str]] = None,
        include_reason: bool = True,
        async_mode: bool = True,
        strict_mode: bool = False,
        verbose_mode: bool = False,
    ):
        self.threshold = 0 if strict_mode else threshold
        self.model = model
        self.include_reason = include_reason
        self.async_mode = async_mode
        self.strict_mode = strict_mode
        self.verbose_mode = verbose_mode

    def measure_zh(self, test_case: Dict):

        prompt: dict = AnswerRelevancyTemplate.generate_score_zh(
            input=test_case["input"],
            actual_output=test_case["actual_output"],
        )

        req = {"inputs": prompt, "parameters": {"max_new_tokens": 5, "do_sample": False}}
        try:
            response = requests.post(self.model, headers={"Content-Type": "application/json"}, data=json.dumps(req))
            response.raise_for_status()
            response = response.json()
            score = int(response["generated_text"].strip())
            return score
        except Exception as e:
            print(str(e))

        return 0.0
