# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/"


def getReqData():
    return {
        "text": "What is the revenue of Nike in last 10 years before 2023? Give me detail,more than 1024 words",
        "parameters": {"max_new_tokens": 128, "do_sample": True},
    }


def respStatics(environment, resp):
    return token.respStatics(environment, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
