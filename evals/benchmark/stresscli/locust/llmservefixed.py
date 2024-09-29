# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging

import numpy
import tokenresponse as token

console_logger = logging.getLogger("locust.stats_logger")


def getUrl():
    return "/v1/chat/completions"


def getReqData():
    return {"messages": [{"role": "user", "content": "What is Deep Learning?"}], "model": "tgi", "max_tokens": 128, "n": 1, "stream": True,}



def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
