FROM ubuntu:22.04

WORKDIR /home/user

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.11  \
    python3-pip \
    libpoppler-cpp-dev \
    wget \
    git \
    poppler-utils \
    libmkl-dev \
    curl

COPY requirements.txt /home/user/requirements.txt

RUN pip install -r requirements.txt

RUN cd /home/user/ && \
    git clone https://github.com/opea-project/GenAIEval.git

ENV PYTHONPATH=$PYTHONPATH:/home/user/GenAIEval/

WORKDIR /home/user
