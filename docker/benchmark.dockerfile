#FROM python:3.11-slim AS base
#ARG BASE_TAG=latest
#FROM opea/comps-base:$BASE_TAG
FROM ubuntu:24.04

ENV LANG=en_US.UTF-8
ARG REPO=https://github.com/opea-project/GenAIEval.git
ARG REPO_PATH=""
ARG BRANCH=main

RUN DEBIAN_FRONTEND=noninteractive \ 
    apt-get update && \
    apt-get -y install git python3-pip python3-setuptools

# Download code
SHELL ["/bin/bash", "--login", "-c"]
RUN mkdir -p /GenAIEval
COPY ${REPO_PATH} /GenAIEval
RUN if [ "$REPO_PATH" == "" ]; then rm -rf /GenAIEval/* && rm -rf /GenAIEval/.* ; git clone --single-branch --branch=${BRANCH} ${REPO} /GenAIEval ; fi

# Build From Source
RUN cd /GenAIEval && \
    pip3 install -r requirements.txt  --break-system-packages && \
    python3 setup.py install && \
    pip3 list

WORKDIR /GenAIEval/evals/benchmark
