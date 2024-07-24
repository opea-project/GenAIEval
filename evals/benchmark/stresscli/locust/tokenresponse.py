import numpy
import logging

console_logger = logging.getLogger("locust.stats_logger")

def testFunc():
    print("TestFunc from token_response")

def respStatics(environment, resp):
    #######About the statistic data calculation######
    #Note: Locust statistic data include all requests, failed request may impact the correctness
    #Here we only statistic for success response(Http 2xx/3xx)
    #
    # Token count         : measured by analysis the response content
    # First token latency : measured by response.elapsed, "measures the time taken between sending
    #                       the first byte of the request and finishing parsing the headers."
    #                       https://requests.readthedocs.io/en/latest/api/#requests.Response.elapsed
    # Next token latency  : request_meta['response_time'], reuse and align with locust extention 
    #                       https://github.com/locustio/locust/blob/master/locust/clients.py#L193
    return {'tokens': resp.text.count('data: b'),
            'first_token': resp.elapsed.total_seconds() * 1000,
            'next_token': resp.request_meta['response_time'] -
            resp.elapsed.total_seconds() * 1000}

def staticsOutput(environment,reqlist):
    first_token = []
    next_token = []
    avg_token = []
    e2e_lat = []
    tokens = 0
    duration =environment.runner.stats.last_request_timestamp - environment.runner.stats.start_time

    if len(reqlist) == 0:
        logging.debug(f"len(reqlist): {len(reqlist)}, skip printing")
        return
    for req in iter(reqlist):
        first_token.append(req['first_token'])
        if req['tokens'] != 0:
            next_token.append(req['next_token']/(req['tokens']-1))
            avg_token.append((req['first_token']+req['next_token'])/req['tokens'])
        e2e_lat.append(req['first_token']+req['next_token'])
        tokens += req['tokens']

    #Statistics for success response data only
    if tokens == 0:
        req_msg=     ("Succeed Response:  {} (Total {}, {:.1%} Success), Duration: {:.2f}s, RPS: {:.2f}")
    else:
        req_msg=     ("Succeed Response:  {} (Total {}, {:.1%} Success), Duration: {:.2f}s, Tokens: {},"
                    " RPS: {:.2f}, Tokens per Second: {:.2f}")
    e2e_msg=     "End to End latency(ms),    P50: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    first_msg=   "First token latency(ms),   P50: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    next_msg=    "Average Next token latency(ms): {:.2f}"
    average_msg= "Average token latency(ms)     : {:.2f}"
    console_logger.warning("\n=================Total statistics=====================")
    if tokens == 0:
        console_logger.warning(req_msg.format(len(reqlist),environment.runner.stats.num_requests,
            len(reqlist)/environment.runner.stats.num_requests,duration, len(reqlist)/duration))
    else:
        console_logger.warning(req_msg.format(len(reqlist),environment.runner.stats.num_requests,
            len(reqlist)/environment.runner.stats.num_requests,duration,
            tokens, len(reqlist)/duration, tokens/duration))
    console_logger.warning(e2e_msg.format(numpy.percentile(e2e_lat, 50), numpy.percentile(e2e_lat, 99),
                                          numpy.average(e2e_lat)))
    if tokens != 0:
        console_logger.warning(first_msg.format(numpy.percentile(first_token, 50),
                                                numpy.percentile(first_token, 99),
                                                numpy.average(first_token)))
        console_logger.warning(next_msg.format(numpy.average(next_token)))
        console_logger.warning(average_msg.format(numpy.average(avg_token)))
    console_logger.warning("======================================================\n\n")
    logging.shutdown()
