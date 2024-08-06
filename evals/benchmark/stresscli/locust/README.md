# locust scripts for OPEA ChatQnA

Locust is an open source performance/load testing tool for HTTP and other protocols. Its developer-friendly approach lets you define your tests in regular Python code.

Locust tests can be run from command line or using its web-based UI. Throughput, response times and errors can be viewed in real time and/or exported for later analysis.

You can import regular Python libraries into your tests, and with Locust's pluggable architecture it is infinitely expandable. Unlike when using most other tools, your test design will never be limited by a GUI or domain-specific language.

To get started right away, head over to the [documentation](http://docs.locust.io/en/stable/installation.html).

## Configuration file

locust.conf for configuration, need to modify this file to meet your requirement
```
#Locust script file
locustfile = locustfile.py
#Run without html UI
headless = true
#Target address and port
host = http://10.233.23.72:8888
#Conncurrency numbers
users = 16
#Advice same with users, means no request shape required, and spawn to max at beginning
spawn-rate = 16
#Set to a longer time, since max-request parameter will stop the benchmark
run-time = 100m
#After this number of request issued, benchmark will stopped
max-request = 16
#Only log summary info
only-summary = true
```

## Basic Usage

```
   pip install locust numpy
   locust
```

  This runs a benchmark using parameters defined in locust.conf

  Output:
```
locust is working ...

Concurrency       : 4
Max request count : 8

Exceed the max-request number:8 , Exit...
=================Total statistics=====================
Succeed Response:  8 (Total 8, 100.0% Success), Duration: 81.14s, Tokens: 1024, RPS: 0.10, Tokens per Second: 12.62
End to End latency(ms),    P50: 39860.39,   P99: 45768.89
First token latency(ms),   P50: 6839.28,   P99: 11074.14
Average Next token latency(ms): 255.71
Average token latency(ms)     : 308.90
======================================================


[2024-07-11 08:36:37,795] node1/INFO/locust.main: Shutting down (exit code 0)
Type     Name                              # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s
--------|--------------------------------|-------|-------------|-------|-------|-------|-------|--------|-----------
POST     /v1/chatqna                            8     0(0.00%) |  39539   32856   45833  36000 |    0.10        0.00
--------|--------------------------------|-------|-------------|-------|-------|-------|-------|--------|-----------
         Aggregated                             8     0(0.00%) |  39539   32856   45833  36000 |    0.10        0.00

Response time percentiles (approximated)
Type     Name                        50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|----------------------|--------|------|------|------|------|------|------|------|------|------|------|------
POST     /v1/chatqna               44000  45000  45000  45000  46000  46000  46000  46000  46000  46000  46000      8
--------|----------------------|--------|------|------|------|------|------|------|------|------|------|------|------
         Aggregated                44000  45000  45000  45000  46000  46000  46000  46000  46000  46000  46000      8

```
