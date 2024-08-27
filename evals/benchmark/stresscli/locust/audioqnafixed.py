# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/audioqna"


def getReqData():
    return {"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens": 64}


def respStatics(environment, reqData, resp):
    return token.respStatics(environment, reqData, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
