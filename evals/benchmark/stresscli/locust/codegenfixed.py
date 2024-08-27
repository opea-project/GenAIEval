# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/codegen"


def getReqData():
    return {"messages": "What is the revenue of Nike in last 10 years before 2023? Give me detail", "max_tokens": 128}


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
