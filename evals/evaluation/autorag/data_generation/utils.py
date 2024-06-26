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
import argparse
import json
import random

import jsonlines
import numpy
import requests


def similarity_score(queries, passages, model):
    queries = [queries]
    passages = passages
    instruction = ""
    q_embeddings = model.encode([instruction + q for q in queries], normalize_embeddings=True)
    p_embeddings = model.encode(passages, normalize_embeddings=True)
    similarity_score = q_embeddings @ p_embeddings.T
    return similarity_score


def similarity_check(file_jsonl_path, file_json_split_path, model, similarity_threshold):
    with open(file_jsonl_path) as file:
        for stu in jsonlines.Reader(file):
            stu["query"] = stu["query"].split("?")[:-1]
            for query in stu["query"]:
                query = query.lstrip("0123456789-. ") + "?"
                if similarity_score(query, stu["pos"], model) >= similarity_threshold:
                    data = {
                        "query": query,
                        "pos": stu["pos"],
                        "neg": stu["neg"],
                    }
                    with jsonlines.open(file_json_split_path, "a") as file_json:
                        file_json.write(data)
