# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os

import tokenresponse as token

cwd = os.path.dirname(__file__)
filename = f"{cwd}/../dataset/codetrans.json"
qdict = {}
try:
    with open(filename) as qfile:
        qdict = json.load(qfile)
except:
    logging.error(f"Code Translation File open failed: {filename}")
    exit()


def getUrl():
    return "/v1/codetrans"


def getReqData():
    prompt_length = "100"
    return qdict[prompt_length]


def respStatics(environment, resp):
    return token.respStatics(environment, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
