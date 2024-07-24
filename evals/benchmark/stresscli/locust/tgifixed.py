import tokenresponse as token
import logging
import numpy

console_logger = logging.getLogger("locust.stats_logger")

def getUrl():
    return "/generate"

def getReqData():
    return {"inputs":"What is Machine Learning?",
            "parameters":{"max_new_tokens":17, "do_sample": True}}

def respStatics(environment, resp):
    global metrics_list
    global tgi_metrics

    tgi_metrics = {'total_time':     int(resp.headers['x-total-time']),
                   'queue_time':     int(resp.headers['x-queue-time']),
                   'gtokens':        int(resp.headers['x-generated-tokens']),
                   'time_per_token': int(resp.headers['x-time-per-token'])}
    general_metrics = token.respStatics(environment, resp)
    tgi_metrics.update(general_metrics)
    return tgi_metrics
#    return ""

def staticsOutput(environment,reqlist):
    gtokens = []
    time_per_token = []
    queue_time = []

    token.staticsOutput(environment, reqlist)

    if len(reqlist) == 0:
        logging.debug(f"len(reqlist): {len(reqlist)}, skip printing")
        return
    for req in iter(reqlist):
        gtokens.append(req['gtokens'])
        time_per_token.append(req['time_per_token'])
        queue_time.append(req['queue_time'])
    qtime_msg=  "Queue time(ms),              P50: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    tptk_msg=   "Average token latency(ms),   P50: {:.2f},   P99: {:.2f},   Avg: {:.2f}"
    gtk_msg=    "Generated Token count,       Avg: {:.2f}"
    console_logger.warning("\n=================TGI statistics=====================")
    console_logger.warning(qtime_msg.format(numpy.percentile(queue_time, 50), numpy.percentile(queue_time, 99),
                                          numpy.average(queue_time)))
    console_logger.warning(tptk_msg.format(numpy.percentile(time_per_token, 50), 
                                            numpy.percentile(time_per_token, 99),
                                            numpy.average(time_per_token)))
    console_logger.warning(gtk_msg.format(numpy.average(gtokens)))
    console_logger.warning("======================================================\n\n")
    logging.shutdown()