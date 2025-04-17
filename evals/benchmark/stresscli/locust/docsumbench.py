# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import tokenresponse as token

cwd = os.path.dirname(__file__)
filepath = os.environ["OPEA_EVAL_DATASET"]
filename = os.path.basename(filepath)
max_tokens = os.environ["OPEA_EVAL_MAX_OUTPUT_TOKENS"]
summary_type = os.environ["OPEA_EVAL_SUMMARY_TYPE"]
stream = os.environ["OPEA_EVAL_STREAM"]


def getUrl():
    return "/v1/docsum"


def getReqData():

    files = {
        "type": (None, "text"),
        "messages": (None, ""),
        "files": (filename, open(filepath, "rb"), "text/plain"),
        "max_tokens": (None, max_tokens),
        "language": (None, "en"),
        "summary_type": (None, summary_type),
        "stream": (None, stream),
    }

    return files


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
