# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os

import tokenresponse as token
from langchain_core.prompts import PromptTemplate

retrieval_k = None
rerank_top_n = None
chat_template = None

opea_eval_prompts = os.environ["OPEA_EVAL_PROMPTS"]
max_new_tokens = int(os.environ["OPEA_EVAL_MAX_OUTPUT_TOKENS"])
if "OPEA_EVAL_RETRIEVAL_K" in os.environ:
    retrieval_k = int(os.environ["OPEA_EVAL_RETRIEVAL_K"])
if "OPEA_EVAL_RERANK_TOP_N" in os.environ:
    rerank_top_n = int(os.environ["OPEA_EVAL_RERANK_TOP_N"])

if "OPEA_EVAL_CHAT_TEMPLATE" in os.environ:
    prompt_template = PromptTemplate.from_template(os.environ["OPEA_EVAL_CHAT_TEMPLATE"])
    input_variables = prompt_template.input_variables
    if "question" not in input_variables:
        logging.error('ignore wrong chat_template, at least "question" variable is required')
    else:
        chat_template = os.environ["OPEA_EVAL_CHAT_TEMPLATE"]


def getUrl():
    return "/v1/chatqna"


def getReqData():
    global opea_eval_prompts
    global max_new_tokens
    global retrieval_k
    global rerank_top_n
    global chat_template

    if opea_eval_prompts == "none":
        opea_eval_prompts = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Please answer me the question what is artificial intelligence in detail."
    req_data = {"messages": opea_eval_prompts, "max_tokens": max_new_tokens, "temperature": 0}
    if retrieval_k and retrieval_k > 0:
        req_data["k"] = retrieval_k
    if rerank_top_n and rerank_top_n > 0:
        req_data["top_n"] = rerank_top_n
    if chat_template:
        req_data["chat_template"] = chat_template
    logging.info(f"Generated request data : {req_data}")

    return req_data


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
