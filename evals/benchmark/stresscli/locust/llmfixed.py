# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/chat/completions"


def getReqData():
    return {
        "query": "What is the revenue of Nike in last 10 years before 2023? Give me detail",
        "max_new_tokens": 128,
    }


def respStatics(environment, resp):
    return token.respStatics(environment, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
