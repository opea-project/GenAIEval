# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import re

import numpy as np
import pandas as pd
import yaml
from jinja2 import Template
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error


def load_jsonl(data_path):
    result = []
    with open(data_path, "r") as f:
        for line in f:
            data = json.loads(line)
            result.append(data)
    return result


def load_config(config_path):

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    return config


def compute_mse(x, y):
    return mean_squared_error(x, y)


def compute_pearson(x, y):
    corr, _ = pearsonr(x, y)
    return corr


def extract_delay_from_rate_limit_error_msg(text):
    import re

    pattern = r"retry after (\d+)"
    match = re.search(pattern, text)
    if match:
        retry_time_from_message = match.group(1)
        return float(retry_time_from_message)
    else:
        return 5


def render_prompt(template: Template, **kwargs) -> str:
    text = template.render(**kwargs)
    return text


def extract_score(pattern: str, text: str):
    match = re.search(pattern, text.lower())

    if match:
        score = int(match.group(1))
    else:
        score = 1

    return score


def compute_metric_wise_assessment(metrics, groundtruth, prediction):
    fine_grained_evaluation = pd.DataFrame(index=metrics)
    for i, metric in enumerate(metrics):
        fine_grained_evaluation.loc[metric, "MSE"] = compute_mse(groundtruth[i], prediction[i])
        abs_diff = [abs(g - p) for g, p in zip(groundtruth[i], prediction[i])]
        for diff in [0, 1, 2]:
            fine_grained_evaluation.loc[metric, "|label - score| <= {}".format(diff)] = sum(
                val <= diff for val in abs_diff
            )
    return fine_grained_evaluation


def compute_weighted_assessment(weights, groundtruth, prediction):
    weights, groundtruth, prediction = np.array(weights), np.array(groundtruth), np.array(prediction)
    weighted_labels = np.sum(weights[:, np.newaxis] * groundtruth, axis=0)
    weighted_scores = np.sum(weights[:, np.newaxis] * prediction, axis=0)
    mse = compute_mse(weighted_labels, weighted_scores)
    pearson_correlation = compute_pearson(weighted_labels, weighted_scores)
    return mse, pearson_correlation
