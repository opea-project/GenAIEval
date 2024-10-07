# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/chat/completions"


def getReqData():
    return {
        "query": "What is the revenue of Nike in last 10 years before 2023? Give me detail",
        "max_new_tokens": 128,
        "top_k": 10,
        "top_p": 0.95,
        "typical_p": 0.95,
        "temperature": 0.01,
        "repetition_penalty": 1.03,
        "streaming": True,
    }


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
