#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import torch
from modelscope import AutoModelForCausalLM, AutoTokenizer  # pylint: disable=E0401
import jsonlines
import re
import logging
from .prompt_dict import TRUTHGENERATE_PROMPT


def load_documents(document_file_jsonl_path):
    document_list = []
    with open(document_file_jsonl_path) as file:
        for stu in jsonlines.Reader(file):
            passages = [stu["query"], stu["pos"][0]]
            document_list.append(passages)
    return document_list


def answer_generate(llm, base_dir, file_json_path, generation_config):
    documents = load_documents(base_dir)
    
    try:
        if isinstance(input, str):
            use_endpoint=False
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            llm = AutoModelForCausalLM.from_pretrained(model_id, device_map='auto', torch_dtype=torch.float16)
            model.eval()
        else:
            use_endpoint = True
            llm = llm
    except:
        print("Please check the setting llm!")

    for question, context in enumerate(documents):
        if context and question:
            input = TRUTHGENERATE_PROMPT.format(question=question, context=context)
            if not use_endpoint:
                with torch.no_grad():
                    model_input = tokenizer(input, return_tensors="pt")
                    res = llm.generate(**model_input, generation_config=generation_config)[0]
                    res = tokenizer.decode(res, skip_special_tokens=True)
            else:
                res = llm.invoke(prompt)

            res = res[res.find('Generated ground_truth:'):]
            res = re.sub('Generated ground_truth:', '', res)
            res = re.sub('---', '', res)

            result_str = res.replace('#', " ").replace(r'\t', " ").replace('\n', ' ').replace('\n\n', ' ').strip()

            if result_str and result_str.isspace() == False:
                data = {
                    "question": question,
                    "context": [context],
                    "ground_truth": result_str,
                }
            with jsonlines.open(file_json_path, "a") as file_json:
                file_json.write(data)