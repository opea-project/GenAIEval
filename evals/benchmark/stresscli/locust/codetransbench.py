# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import random

import tokenresponse as token

cwd = os.path.dirname(__file__)
filename = f"{cwd}/../dataset/chatqna.json"
qlist = []
try:
    with open(filename) as qfile:
        qlist = json.load(qfile)
except:
    logging.error(f"Question File open failed: {filename}")
    exit()


def getUrl():
    return "/v1/chatqna"


def getReqData():
    qid = random.randint(1, 189)
    logging.debug(f"Selected question: {qlist[qid]['qText']}")

    return {"messages": qlist[qid]["qText"], "max_tokens": 128}


def respStatics(environment, resp):
    return token.respStatics(environment, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
