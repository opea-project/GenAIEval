FROM vault.habana.ai/gaudi-docker/1.18.0/ubuntu22.04/habanalabs/pytorch-installer-2.4.0:latest as hpu

ENV LANG=en_US.UTF-8
ENV PYTHONPATH=/root:/usr/lib/habanalabs/
ARG REPO=https://github.com/intel/genaieval.git
ARG REPO_PATH=""
ARG BRANCH=main

RUN apt-get update && \
    apt-get install git-lfs && \
    git-lfs install

# Download code
SHELL ["/bin/bash", "--login", "-c"]
RUN mkdir -p /genaieval
COPY ${REPO_PATH} /genaieval
RUN if [ "$REPO_PATH" == "" ]; then rm -rf /genaieval/* && rm -rf /genaieval/.* ; git clone --single-branch --branch=${BRANCH} ${REPO} /genaieval ; fi

# Build From Source
RUN pip install --upgrade pip setuptools==69.5.1
RUN cd /genaieval && \
    pip install -r requirements.txt && \
    python setup.py install && \
    pip install --upgrade-strategy eager optimum[habana] && \
    pip list

WORKDIR /genaieval/
