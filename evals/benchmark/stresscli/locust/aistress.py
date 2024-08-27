# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys
import threading
import time

import gevent
import numpy
import sseclient
from locust import HttpUser, between, events, task
from locust.runners import STATE_CLEANUP, STATE_STOPPED, STATE_STOPPING, MasterRunner, WorkerRunner

cwd = os.path.dirname(__file__)
sys.path.append(cwd)


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--max-request",
        type=int,
        env_var="MAX_REQUEST",
        default=10000,
        help="Stop the benchmark If exceed this request",
    )
    parser.add_argument(
        "--http-timeout", type=int, env_var="HTTP_TIMEOUT", default=120000, help="Http timeout before receive response"
    )
    parser.add_argument(
        "--bench-target",
        type=str,
        env_var="BENCH_TARGET",
        default="chatqnafixed",
        help="python package name for benchmark target",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        env_var="LLM_MODEL",
        default="Intel/neural-chat-7b-v3-3",
        help="LLM model name",
    )


reqlist = []
start_ts = 0
end_ts = 0
req_total = 0
last_resp_ts = 0

bench_package = ""
console_logger = logging.getLogger("locust.stats_logger")


class AiStressUser(HttpUser):
    request = 0
    _lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @task
    def bench_main(self):

        if AiStressUser.request >= self.environment.parsed_options.max_request:
            time.sleep(1)
            return
        with AiStressUser._lock:
            AiStressUser.request += 1
            self.environment.runner.send_message("worker_reqsent", 1)
        reqData = bench_package.getReqData()
        url = bench_package.getUrl()
        try:
            start_ts = time.perf_counter()
            with self.client.post(
                url,
                json=reqData,
                stream=True,
                catch_response=True,
                timeout=self.environment.parsed_options.http_timeout,
            ) as resp:
                logging.debug("Got response...........................")

                if resp.status_code >= 200 and resp.status_code < 400:
                    if self.environment.parsed_options.bench_target in [
                        "audioqnafixed",
                        "audioqnabench",
                    ]:  # non-stream case
                        respData = {
                            "response_string": resp.text,
                            "first_token_latency": time.perf_counter() - start_ts,
                            "total_latency": time.perf_counter() - start_ts,
                        }
                    else:
                        first_token_ts = None
                        client = sseclient.SSEClient(resp)
                        complete_response = ""
                        for event in client.events():
                            if event.data == "[DONE]":
                                break
                            else:
                                if first_token_ts is None:
                                    first_token_ts = time.perf_counter()
                                chunk = event.data.strip()
                                if chunk.startswith("b'") and chunk.endswith("'"):
                                    chunk = chunk[2:-1]
                            complete_response += chunk
                        end_ts = time.perf_counter()
                        respData = {
                            "response_string": complete_response,
                            "first_token_latency": first_token_ts - start_ts,
                            "total_latency": end_ts - start_ts,
                        }
                    reqdata = bench_package.respStatics(self.environment, reqData, respData)
                    logging.debug(f"Request data collected {reqdata}")
                    self.environment.runner.send_message("worker_reqdata", reqdata)
            logging.debug("Finished response analysis...........................")
        except Exception as e:
            # In case of exception occurs, locust lost the statistic for this request.
            # Consider as a failed request, and report to Locust statistics
            logging.error(f"Failed with request : {e}")
            self.environment.runner.stats.log_request("POST", url, time.perf_counter() - start_ts, 0)
            self.environment.runner.stats.log_error("POST", url, "Locust Request error")

    # def on_stop(self) -> None:


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        console_logger.info(f"Concurrency       : {environment.parsed_options.num_users}")
        console_logger.info(f"Max request count : {environment.parsed_options.max_request}")
        console_logger.info(f"Http timeout      : {environment.parsed_options.http_timeout}\n")
        console_logger.info(f"Benchmark target  : {environment.parsed_options.bench_target}\n")


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    global bench_package
    try:
        bench_package = __import__(environment.parsed_options.bench_target)
    except ImportError:
        return None
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
        environment.runner.register_message("worker_reqdata", on_reqdata)
        environment.runner.register_message("worker_reqsent", on_reqsent)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("all_reqcnt", on_reqcount)


@events.quitting.add_listener
def on_locust_quitting(environment, **kwargs):
    if isinstance(environment.runner, WorkerRunner):
        logging.debug("Running in WorkerRunner, DO NOT print statistics")
        return

    logging.debug("#####Running in MasterRunner, DO print statistics")
    bench_package.staticsOutput(environment, reqlist)


def on_reqdata(msg, **kwargs):
    logging.debug(f"Request data: {msg.data}")
    reqlist.append(msg.data)


def on_reqsent(environment, msg, **kwargs):
    logging.debug(f"request sent: {msg.data}")
    global req_total
    req_total += 1
    environment.runner.send_message("all_reqcnt", req_total)


def on_reqcount(msg, **kwargs):
    logging.debug(f"Update total request: {msg.data}")
    AiStressUser.request = msg.data


def checker(environment):
    while environment.runner.state not in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        time.sleep(1)
        if environment.runner.stats.num_requests >= environment.parsed_options.max_request:
            logging.info(f"Exceed the max-request number:{environment.runner.stats.num_requests}, Exit...")
            #            while environment.runner.user_count > 0:
            time.sleep(5)
            environment.runner.quit()
            return
