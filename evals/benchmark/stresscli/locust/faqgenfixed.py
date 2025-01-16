# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/faqgen"


def getReqData():
    return {
        "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E6.",
        "max_tokens": 128,
        "top_k": 1,
    }


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
