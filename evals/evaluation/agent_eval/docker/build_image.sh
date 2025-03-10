# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

dockerfile=Dockerfile

docker build \
    --no-cache \
    -f ${dockerfile} . \
    -t agent-eval:latest \
    --network=host \
    --build-arg http_proxy=${http_proxy} \
    --build-arg https_proxy=${https_proxy} \
    --build-arg no_proxy=${no_proxy} \
