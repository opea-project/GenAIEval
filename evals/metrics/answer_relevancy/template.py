# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class AnswerRelevancyTemplate:
    @staticmethod
    def generate_score_zh(input: str, actual_output: str):
        return f"""请你评估以下两个句子的相关性,并给出相关性评分,评分从最低的1到最高的5。
请按以下评估步骤进行评估:
1. 仔细阅读给定的两个句子。
2. 比较两个句子的相关性。
3. 给出从1到5的相关性评分。
以下是句子1:
{input}
以下是句子2:
{actual_output}
请按要求给出你的评分:
"""
