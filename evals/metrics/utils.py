# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Any, List, Optional, Tuple, Union

import evaluate
import jieba
from pydantic import BaseModel


def trimAndLoadJson(input_string: str, metric=None) -> Any:
    start = input_string.find("{")
    end = input_string.rfind("}") + 1

    if end == 0 and start != -1:
        input_string = input_string + "}"
        end = len(input_string)

    jsonStr = input_string[start:end] if start != -1 and end != 0 else ""

    try:
        return json.loads(jsonStr)
    except json.JSONDecodeError:
        error_str = "Evaluation LLM outputted an invalid JSON. Please use a better evaluation model."
        if metric is not None:
            metric.error = error_str
        raise ValueError(error_str)
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")


def construct_verbose_logs(metric, steps: List[str]) -> str:
    verbose_logs = ""
    for i in range(len(steps) - 1):
        verbose_logs += steps[i]

        # don't add new line for penultimate step
        if i < len(steps) - 2:
            verbose_logs += "\n\n"

    if metric.verbose_mode:
        # only print reason and score for deepeval
        print_verbose_logs(metric.__name__, verbose_logs + f"\n\n{steps[-1]}")

    return verbose_logs


def prettify_list(lst: List[Any]):
    if len(lst) == 0:
        return "[]"

    formatted_elements = []
    for item in lst:
        if isinstance(item, str):
            formatted_elements.append(f'"{item}"')
        elif isinstance(item, BaseModel):
            formatted_elements.append(json.dumps(item.dict(), indent=4).replace("\n", "\n    "))
        else:
            formatted_elements.append(repr(item))  # Fallback for other types

    formatted_list = ",\n    ".join(formatted_elements)
    return f"[\n    {formatted_list}\n]"


def print_verbose_logs(metric: str, logs: str):
    print("*" * 50)
    print(f"{metric} Verbose Logs")
    print("*" * 50)
    print("")
    print(logs)
    print("")
    print("=" * 70)


def catch_all_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(repr(e))

    return wrapper


tokenizer = lambda text: list(jieba.cut(text))


@catch_all_exceptions
def bleu_score(continuation: str, reference: str, with_penalty=False) -> float:
    bleu = evaluate.load(os.path.join(os.path.dirname(__file__), "bleu"))
    results = bleu.compute(predictions=[continuation], references=[[reference]], tokenizer=tokenizer)

    bleu_avg = results["bleu"]
    bleu1 = results["precisions"][0]
    bleu2 = results["precisions"][1]
    bleu3 = results["precisions"][2]
    bleu4 = results["precisions"][3]
    brevity_penalty = results["brevity_penalty"]

    if with_penalty:
        return bleu_avg, bleu1, bleu2, bleu3, bleu4
    else:
        return 0.0 if brevity_penalty == 0 else bleu_avg / brevity_penalty, bleu1, bleu2, bleu3, bleu4


@catch_all_exceptions
def rougeL_score(continuation: str, reference: str) -> float:
    rouge = evaluate.load(os.path.join(os.path.dirname(__file__), "rouge"))
    results = rouge.compute(
        predictions=[continuation], references=[[reference]], tokenizer=tokenizer, rouge_types=["rougeL"]
    )
    score = results["rougeL"]
    return score
