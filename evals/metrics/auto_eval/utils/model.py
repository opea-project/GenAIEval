# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List

import openai
import torch
from huggingface_hub import InferenceClient
from transformers import AutoTokenizer, pipeline

from .helper import extract_delay_from_rate_limit_error_msg
from .retry import retry_and_handle_exceptions


class EndpointEvaluator:
    def __init__(self, model_name):
        self.client = InferenceClient(base_url="{}/v1/chat/completions".format(model_name))

    def generate(self, messages, **kwargs):
        output = self.client.chat.completions.create(
            model="tgi",
            messages=messages,
            stream=True,
            **kwargs,
        )
        response = [chunk.choices[0].delta.content for chunk in output]
        response = [content for content in response if content]
        response = " ".join(response)
        return response


class HFEvaluator:
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        device_map = "auto" if torch.cuda.is_available() else "cpu"
        if device_map == "cpu":
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=self.tokenizer,
                torch_dtype=torch.bfloat16,
                device_map="cpu",
            )
        else:
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=self.tokenizer,
                torch_dtype=torch.float16,
                device_map="auto",
            )

    def generate(self, messages, **kwargs) -> List[float]:

        prompt = self.pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        outputs = self.pipe(prompt, **kwargs, return_full_text=False)
        result = outputs[0]["generated_text"]
        return result


class OAIEvaluator:
    def __init__(self, openai_key, model_name):
        openai.api_key = openai_key
        self.model_name = model_name

    @retry_and_handle_exceptions(
        exception_to_check=(
            openai.RateLimitError,
            openai.APIError,
            KeyError,
        ),
        max_retries=5,
        extract_delay_from_error_message=extract_delay_from_rate_limit_error_msg,
    )
    def generate(self, messages: list, **kwargs) -> List[float]:
        return (
            openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **kwargs,
            )
            .choices[0]
            .message.content
        )
