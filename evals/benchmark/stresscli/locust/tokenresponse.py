# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging

import numpy
import transformers

console_logger = logging.getLogger("locust.stats_logger")


def testFunc():
    print("TestFunc from token_response")


def respStatics(environment, req, resp):
    if not hasattr(environment, "tokenizer"):
        tokenizer = transformers.AutoTokenizer.from_pretrained(environment.parsed_options.llm_model)
    else:
        tokenizer = environment.tokenizer

    if environment.parsed_options.bench_target in [
        "chatqnafixed",
        "chatqnabench",
        "faqgenfixed",
        "faqgenbench",
        "codegenfixed",
        "codegenbench",
        "chatqna_qlist_pubmed",
    ]:
        num_token_input_prompt = len(tokenizer.encode(req["messages"]))
    elif environment.parsed_options.bench_target in [
        "codetransfixed",
        "codetransbench",
    ]:
        req_str = json.dumps(req)
        num_token_input_prompt = len(tokenizer.encode(req_str))
    elif environment.parsed_options.bench_target in [
        "docsumfixed",
        "docsumbench",
    ]:
        file_obj = req["files"][1]
        file_path = file_obj.name
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
        num_token_input_prompt = len(tokenizer.encode(file_content))
    elif environment.parsed_options.bench_target in ["llmfixed"]:
        num_token_input_prompt = len(tokenizer.encode(req["query"]))
    elif environment.parsed_options.bench_target == "llmservefixed":
        content = " ".join([msg["content"] for msg in req["messages"]])
        num_token_input_prompt = len(tokenizer.encode(content))
    else:
        num_token_input_prompt = -1

    num_token_output = len(
        tokenizer.encode(resp["response_string"].encode("utf-8").decode("unicode_escape"), add_special_tokens=False)
    )

    return {
        "tokens_input": num_token_input_prompt,
        "tokens_output": num_token_output,
        "first_token": resp["first_token_latency"] * 1000,
        "next_token": (resp["total_latency"] - resp["first_token_latency"]) / (num_token_output - 1) * 1000,
        "total_latency": resp["total_latency"] * 1000,
        "test_start_time": resp["test_start_time"],
    }


def staticsOutput(environment, reqlist):
    first_token = []
    next_token = []
    avg_token = []
    e2e_lat = []
    tokens_input = 0
    tokens_output = 0

    if len(reqlist) == 0:
        logging.debug(f"len(reqlist): {len(reqlist)}, skip printing")
        return
    for req in iter(reqlist):
        first_token.append(req["first_token"])
        if req["tokens_output"] != 0:
            next_token.append(req["next_token"])
            avg_token.append((req["total_latency"]) / req["tokens_output"])
        e2e_lat.append(req["total_latency"])
        tokens_output += req["tokens_output"]
        tokens_input += req["tokens_input"]
        test_start_time = req["test_start_time"]
    duration = environment.runner.stats.last_request_timestamp - environment.runner.stats.start_time

    # Statistics for success response data only
    if tokens_output == 0:
        req_msg = "Succeed Response:  {} (Total {}, {:.1%} Success), Duration: {:.2f}s, RPS: {:.2f}"
    else:
        req_msg = (
            "Succeed Response:  {} (Total {}, {:.1%} Success), Duration: {:.2f}s, Input Tokens: {},"
            " Output Tokens: {}, RPS: {:.2f}, Input Tokens per Second: {:.2f}, Output Tokens per Second: {:.2f}"
        )
    e2e_msg = "End to End latency(ms),    P50: {:.2f},   P90: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    first_msg = "Time to First Token-TTFT(ms),   P50: {:.2f},   P90: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    next_msg = "Time Per Output Token-TPOT(ms),   P50: {:.2f},   P90: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    average_msg = "Average token latency(ms)     : {:.2f}"
    console_logger.warning("\n=================Total statistics=====================")
    if tokens_output == 0:
        console_logger.warning(
            req_msg.format(
                len(reqlist),
                environment.runner.stats.num_requests,
                len(reqlist) / environment.runner.stats.num_requests,
                duration,
                len(reqlist) / duration,
            )
        )
    else:
        console_logger.warning(
            req_msg.format(
                len(reqlist),
                environment.runner.stats.num_requests,
                len(reqlist) / environment.runner.stats.num_requests,
                duration,
                tokens_input,
                tokens_output,
                len(reqlist) / duration,
                tokens_input / duration,
                tokens_output / duration,
            )
        )
    console_logger.warning(
        e2e_msg.format(
            numpy.percentile(e2e_lat, 50),
            numpy.percentile(e2e_lat, 90),
            numpy.percentile(e2e_lat, 99),
            numpy.average(e2e_lat),
        )
    )
    if tokens_output != 0:
        console_logger.warning(
            first_msg.format(
                numpy.percentile(first_token, 50),
                numpy.percentile(first_token, 90),
                numpy.percentile(first_token, 99),
                numpy.average(first_token),
            )
        )
        console_logger.warning(
            next_msg.format(
                numpy.percentile(next_token, 50),
                numpy.percentile(next_token, 90),
                numpy.percentile(next_token, 99),
                numpy.average(next_token),
            )
        )
        console_logger.warning(average_msg.format(numpy.average(avg_token)))
    console_logger.warning("======================================================\n\n")
    logging.shutdown()


def staticsOutputForMicroservice(environment, reqlist):
    e2e_lat = []
    duration = environment.runner.stats.last_request_timestamp - environment.runner.stats.start_time

    if len(reqlist) == 0:
        logging.debug(f"len(reqlist): {len(reqlist)}, skip printing")
        return
    for req in iter(reqlist):
        e2e_lat.append(req["total_latency"])

    # Statistics for success response data only
    req_msg = "Succeed Response:  {} (Total {}, {:.1%} Success), Duration: {:.2f}s, RPS: {:.2f}"
    e2e_msg = "End to End latency(ms),    P50: {:.2f},   P90: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    console_logger.warning("\n=================Total statistics=====================")
    console_logger.warning(
        req_msg.format(
            len(reqlist),
            environment.runner.stats.num_requests,
            len(reqlist) / environment.runner.stats.num_requests,
            duration,
            len(reqlist) / duration,
        )
    )
    console_logger.warning(
        e2e_msg.format(
            numpy.percentile(e2e_lat, 50),
            numpy.percentile(e2e_lat, 90),
            numpy.percentile(e2e_lat, 99),
            numpy.average(e2e_lat),
        )
    )
    console_logger.warning("======================================================\n\n")
    logging.shutdown()
