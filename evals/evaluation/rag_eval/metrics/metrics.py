#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json

import requests

from .template import CorrelationTemplate


def LLM_score(continuation: str, reference: str, llm_endpoint: str) -> float:
    if llm_endpoint:
        query = CorrelationTemplate.generate_query(continuation, reference)
        req = {"inputs": query, "parameters": {"max_new_tokens": 5, "do_sample": False}}
        try:
            response = requests.post(llm_endpoint, headers={"Content-Type": "application/json"}, data=json.dumps(req))
            response.raise_for_status()
            response = response.json()
            score = int(response["generated_text"].strip())
            return score
        except Exception as e:
            print(str(e))
    return 0.0
