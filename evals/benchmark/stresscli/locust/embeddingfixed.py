# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/embeddings"


def getReqData():
    return {
        "text": "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further."
    }


def respStatics(environment, reqData, resp):
    return {
        "total_latency": resp["total_latency"] * 1000,
    }


def staticsOutput(environment, reqlist):
    token.staticsOutputForMicroservice(environment, reqlist)
