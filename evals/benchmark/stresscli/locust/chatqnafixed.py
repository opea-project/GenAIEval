# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import tokenresponse as token

opea_eval_prompts = os.environ["OPEA_EVAL_PROMPTS"]
max_new_tokens = int(os.environ["OPEA_EVAL_MAX_OUTPUT_TOKENS"])


def getUrl():
    return "/v1/chatqna"


def getReqData():
    global opea_eval_prompts
    global max_new_tokens
    if opea_eval_prompts == "none":
        opea_eval_prompts = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Please answer me the question what is artificial intelligence in detail."
    return {"messages": opea_eval_prompts, "max_tokens": max_new_tokens, "top_k": 1, "temperature": 0}


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
