FROM python:3.11-slim AS base

ENV LANG=en_US.UTF-8
ARG REPO=https://github.com/opea-project/GenAIEval.git
ARG REPO_PATH=""
ARG BRANCH=main

RUN apt-get update && \
    apt-get install git-lfs && \
    git-lfs install

# Download code
SHELL ["/bin/bash", "--login", "-c"]
RUN mkdir -p /GenAIEval
COPY ${REPO_PATH} /GenAIEval
RUN if [ "$REPO_PATH" == "" ]; then rm -rf /GenAIEval/* && rm -rf /GenAIEval/.* ; git clone --single-branch --branch=${BRANCH} ${REPO} /GenAIEval ; fi
RUN pip install --upgrade pip setuptools==69.5.1

# Build From Source
RUN cd /GenAIEval && \
    pip install -r requirements.txt && \
    python setup.py install && \
    pip list

WORKDIR /GenAIEval/
