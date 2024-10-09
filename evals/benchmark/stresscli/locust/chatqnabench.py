# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import random

import tokenresponse as token

cwd = os.path.dirname(__file__)
dataset = os.environ["OPEA_EVAL_DATASET"]
if dataset == "sharegpt":
    filename = f"{cwd}/../dataset/sharegpt.json"
elif dataset == "default":
    filename = f"{cwd}/../dataset/chatqna.json"
else:
    logging.error(f"Dataset not found: dataset/{dataset}.json.")
    exit()

qlist = []
try:
    with open(filename) as qfile:
        qlist = json.load(qfile)
except:
    logging.error(f"Question File open failed: {filename}")
    exit()

seed = os.environ["OPEA_EVAL_SEED"]
if seed and seed != "none":
    random.seed(seed)


def getUrl():
    return "/v1/chatqna"


def getReqData():
    qlen = len(qlist)
    qid = random.randint(0, qlen - 1)

    if dataset == "sharegpt":
        msg = qlist[qid]["conversations"][0]["value"]
    elif dataset == "default":
        msg = qlist[qid]["qText"]
    else:
        msg = qlist[qid]["qText"]

    logging.debug(f"Selected question: {msg}")

    return {"messages": msg, "max_tokens": 128}


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
