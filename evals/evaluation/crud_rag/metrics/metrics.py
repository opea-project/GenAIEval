#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os

import evaluate
import requests

from .template import CorrelationTemplate


def catch_all_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(repr(e))

    return wrapper


@catch_all_exceptions
def bleu_score(continuation: str, reference: str, with_penalty=False) -> float:
    bleu = evaluate.load(os.path.join(os.path.dirname(__file__), "bleu"))
    results = bleu.compute(predictions=[continuation], references=[[reference]])

    bleu_avg = results["bleu"]
    bleu1 = results["precisions"][0]
    bleu2 = results["precisions"][1]
    bleu3 = results["precisions"][2]
    bleu4 = results["precisions"][3]
    brevity_penalty = results["brevity_penalty"]

    if with_penalty:
        return bleu_avg, bleu1, bleu2, bleu3, bleu4
    else:
        return 0.0 if brevity_penalty == 0 else bleu_avg / brevity_penalty, bleu1, bleu2, bleu3, bleu4


@catch_all_exceptions
def rougeL_score(continuation: str, reference: str) -> float:
    rogue = evaluate.load(os.path.join(os.path.dirname(__file__), "rogue"))
    results = rogue.compute(predictions=[continuation], references=[[reference]], rouge_types=["rougeL"])
    score = results["rougeL"]
    return score


@catch_all_exceptions
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
