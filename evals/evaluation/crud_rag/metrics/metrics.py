#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os

import evaluate
import requests


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
        query = f"""请你评估以下两个句子的相关性,并给出相关性评分,评分从最低的1到最高的5。

请按以下评估步骤进行评估:
1. 仔细阅读给定的两个句子。
2. 比较两个句子的相关性。
3. 给出从1到5的相关性评分。

以下是句子1:
{reference}

以下是句子2:
{continuation}

请按要求给出你的评分:
"""
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
