# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import random

import tokenresponse as token

cwd = os.path.dirname(__file__)
filename = f"{cwd}/../dataset/codegen.json"
qdict = {}
try:
    with open(filename) as qfile:
        qdict = json.load(qfile)
except:
    logging.error(f"Question File open failed: {filename}")
    exit()


def getUrl():
    return "/v1/codegen"


def getReqData():
    prompt = "50"
    return {"messages": qdict[prompt], "max_tokens": 128}


def respStatics(environment, resp):
    return token.respStatics(environment, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
