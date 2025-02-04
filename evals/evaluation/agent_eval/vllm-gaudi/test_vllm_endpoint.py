# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from langchain_openai import ChatOpenAI

host_ip = os.getenv("host_ip", "localhost")
model_name = "meta-llama/Meta-Llama-3.1-70B-Instruct"
openai_endpoint = f"http://{host_ip}:8085/v1"
print("LLM endpoint: ", openai_endpoint)
chat_model = ChatOpenAI(
    openai_api_key="EMPTY",
    openai_api_base=openai_endpoint,
    model_name=model_name,
)

print(chat_model.invoke("Hello, how are you?"))
