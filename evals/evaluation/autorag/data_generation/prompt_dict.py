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


QUERYGENERATE_PROMPT = """
Task: You are asked to act as a human annotator. Your role is to generate 2 specific, open-ended questions based on the provided context.
Each question should aim to extract or clarify key information from the context, focusing on a single aspect or detail.
The questions must be directly related to the context to form a query-positive pair, suitable for use in constructing a retrieval dataset.
---
Requirements:
1. Questions should be based on the keywords, such as phrases at the beginning, phrases before colon, and recurring phrases in the context.
2. Use the terms in the context instead of pronouns.
---
Desired format:
1. <question_1>
2. <question_2>
---
### Context:
{context}
---
Generated questions:
"""

TRUTHGENERATE_PROMPT = """
Task: You are asked to act as a human annotator. Your role is to generate the right answer based on the context and question provided.
Answers should aim to extract or clarify the key information of the question from the context, focusing on a single aspect or detail.
The answer must be directly related to the context and the question, suitable for use in constructing a synthetic retrieval evaluation dataset.
---
Desired format:
1. <ground_truth>
---
### Question:
{question}
---
### Context:
{context}
---
Generated ground_truth:
"""
