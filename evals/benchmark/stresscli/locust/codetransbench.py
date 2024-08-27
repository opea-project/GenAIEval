# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import random

import tokenresponse as token

cwd = os.path.dirname(__file__)
filename = f"{cwd}/../dataset/codetrans.json"
qlist = {}
try:
    with open(filename) as qfile:
        qlist = json.load(qfile)
except:
    logging.error(f"Code Translation File open failed: {filename}")
    exit()


def getUrl():
    return "/v1/codetrans"


def getReqData():
    qid = random.randint(0, 5)
    qinput = qlist[qid]["input"]
    logging.debug(f"Selected input code: {qinput}")
    return qinput


def respStatics(environment, resp):
    return token.respStatics(environment, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
