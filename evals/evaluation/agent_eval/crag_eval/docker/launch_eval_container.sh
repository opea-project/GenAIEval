# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

volume=$WORKDIR
host_ip=$(hostname -I | awk '{print $1}')

docker run -it --name crag_eval -v $volume:/home/user/ -e WORKDIR=/home/user -e HF_HOME=/home/user/hf_cache -e host_ip=$host_ip -e http_proxy=$http_proxy -e https_proxy=$https_proxy crag-eval:v1.1
