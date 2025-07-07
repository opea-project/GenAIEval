# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ctypes
import gc

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_SAMPLING_TEMPERATURE = 0.001
DEFAULT_REPETITION_PENTALTY = 1.0
DEFAULT_MAX_NEW_TOKENS = 256
DEFAULT_LLM_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DEFAULT_BM25_WEIGHT = 0.333333


def _load_huggingface_llm(name):
    tokenizer = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        name,
        # load_in_8bit=True,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    # model.to(DEFAULT_LLM_DEVICE)

    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = model.config.eos_token_id
    return model, tokenizer


def load_huggingface_llm(name):
    model, tokenizer = _load_huggingface_llm(name)
    return model, tokenizer


def load_hf_pipeline(name, temperature=DEFAULT_SAMPLING_TEMPERATURE, max_new_tokens=DEFAULT_MAX_NEW_TOKENS):
    hf_model, hf_tokenizer = _load_huggingface_llm(name)
    hf_pipeline = transformers.pipeline(
        task="text-generation",
        model=hf_model,
        tokenizer=hf_tokenizer,
        do_sample=True,  # does not work ... True if temperature > 0 else False,
        temperature=temperature,
        repetition_penalty=DEFAULT_REPETITION_PENTALTY,
        return_full_text=False,
        max_new_tokens=max_new_tokens,
    )
    return hf_pipeline


def clean_memory():
    gc.collect()
    ctypes.CDLL("libc.so.6").malloc_trim(0)
