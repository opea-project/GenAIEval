# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import json
import logging
import os
import random
import urllib.request

import tokenresponse as token

cwd = os.path.dirname(__file__)
filename = f"{cwd}/../dataset/audioqna.json"
qlist = []
try:
    with open(filename) as qfile:
        qlist = json.load(qfile)
except:
    logging.error(f"Input audio File open failed: {filename}")
    exit()


def getUrl():
    return "/v1/audioqna"


def get_byte_str_with_url(url):
    file_name = url.split("/")[-1]
    if not os.path.exists(file_name):
        logging.debug(f"Download {url}...")
        urllib.request.urlretrieve(
            url,
            file_name,
        )
    with open(file_name, "rb") as f:
        test_audio_base64_str = base64.b64encode(f.read()).decode("utf-8")
    return test_audio_base64_str


def getReqData():
    qid = random.randint(1, 4)
    logging.debug(f"Selected audio: {qlist[qid]['qUrl']}")
    qUrl = qlist[qid]["qUrl"]
    base64_str = get_byte_str_with_url(qUrl)

    return {"audio": base64_str, "max_tokens": 64}


def respStatics(environment, reqData, resp):
    return token.respStatics(environment, reqData, resp)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
