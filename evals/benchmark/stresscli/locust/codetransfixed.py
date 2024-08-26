# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/codetrans"


def getReqData():
    return {
        "language_from": "Rust",
        "language_to": "Python",
        "source_code": "'''Rust\nfn main() {\n    let x = 5;\n    let x = x + 1;\n    let x = x * 2;\n    println!(\"The value of x is: {}\", x);\n}'''",
    }


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)
