# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os

import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

RESPONSE_MAP = {"Yes": "True", "It's impossible to say": "Neither", "No": "False", "no": "False", "yes": "True"}


def generate_pred_prob(metric_results_path):
    """Processes a JSON file containing model evaluation results to generate predicted probabilities and labels.

    Parameters:
    metric_results_path (str): The file path to the JSON file containing the evaluation results.

    Returns:
    tuple: A tuple containing:
        - predicted_probabilities (list): A list of predicted probabilities for each evaluation instance.
        - labels (list): A list of true labels for each evaluation instance.
        - num_labels (int): The number of distinct labels or options available.
        - class_label_index_map (dict): A mapping from class indices to class labels, used for interpreting the predicted probabilities.
    """
    if not metric_results_path:
        raise ValueError("The results_path is None or an empty string. Please provide a valid file path.")

    if not os.path.exists(metric_results_path):
        raise FileNotFoundError(f"The file at {metric_results_path} does not exist. Please provide a valid file path.")

    try:
        with open(metric_results_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError("The file content is not a valid JSON array.")

    labels = []
    map_target = False

    num_labels = len(data[0]["arguments"])
    predicted_probabilities = []

    if isinstance(data[0]["target"], list):
        if data[0]["target"][0] in RESPONSE_MAP and data[0]["arguments"][0][1].strip() in RESPONSE_MAP.values():
            map_target = True
    elif data[0]["target"] in RESPONSE_MAP and data[0]["arguments"][0][1].strip() in RESPONSE_MAP.values():
        map_target = True

    if num_labels == 2:
        is_ans_match_type_q = False
        has_diff_labels = False
        are_labels_identical = False
        is_one_based_indexing = False

        if set([i[1] for i in data[1]["arguments"]]) != set([i[1] for i in data[0]["arguments"]]) and isinstance(
            data[0]["target"], str
        ):
            has_diff_labels = True

        if len(set([data[0]["arguments"][0][1], data[0]["arguments"][1][1]])) == 1:
            are_labels_identical = True

            if "answer" in data[0]["doc"]:
                for item in data:
                    ref = item["doc"]["answer"]
                    if isinstance(ref, str):
                        ref = int(ref)

                    if ref >= 2:
                        is_one_based_indexing = True

        if "answer_matching_behavior" in data[0]["doc"]:
            reference_label = data[0]["doc"]["answer_matching_behavior"].strip()
            is_ans_match_type_q = True

        for item in data:
            target_label = item["target"]
            class_label_index_map = {}

            if are_labels_identical:
                if "label" in item["doc"]:
                    target_label = item["doc"]["label"]

                elif "answer" in item["doc"]:
                    target_label = item["doc"]["answer"]
                    if isinstance(target_label, str):
                        target_label = int(target_label)

            if is_one_based_indexing:
                target_label -= 1

            if isinstance(target_label, str):
                target_label = target_label.strip()
            options = [i[1] for i in data[0]["arguments"]]

            if isinstance(target_label, list):
                if map_target:
                    target_label = RESPONSE_MAP[target_label[0]]

                    if set([i[1] for i in data[1]["arguments"]]) != set(options):
                        options = [i for i in range(num_labels)]
                        class_label_index_map = {options[i]: options[i] for i in range(len(options))}

                    else:
                        class_label_index_map = {i: options[i] for i in range(num_labels)}
                else:
                    target_label = target_label[0]
            else:
                if map_target:
                    target_label = RESPONSE_MAP[target_label]
                    class_label_index_map = {i: options[i] for i in range(num_labels)}

                    if set([i[1] for i in data[1]["arguments"]]) != set(options):
                        options = [i for i in range(num_labels)]
                        class_label_index_map = {options[i]: options[i] for i in range(len(options))}

                    else:
                        class_label_index_map = {i: options[i] for i in range(num_labels)}

            if has_diff_labels and not are_labels_identical:
                arguments = [quest[1].strip() for quest in item["arguments"]]

                if isinstance(target_label, int) and (isinstance(arguments[0], str)):
                    target_label = str(target_label)
                try:
                    target_label = arguments.index(target_label)
                except:
                    exit()

            if is_ans_match_type_q and item["arguments"][0][1].strip() != reference_label:

                target_label = 0 if target_label == 1 else 1
                filtered_resps = item["filtered_resps"][::-1]
            else:

                filtered_resps = item["filtered_resps"]

            labels.append(target_label)

            # Convert log likelihoods to probabilities
            log_likelihoods = np.array([resp[0] for resp in filtered_resps]).reshape(1, -1)
            probs = softmax(log_likelihoods, axis=1)[0][1]  # Extract probabilities for the positive class
            predicted_probabilities.append(probs)

    else:
        options = [i[1] for i in data[0]["arguments"]]
        has_diff_labels = False

        if set([i[1] for i in data[1]["arguments"]]) != set(options):
            options = [i for i in range(num_labels)]
            has_diff_labels = True
            class_label_index_map = {options[i]: options[i] for i in range(len(options))}

        else:
            class_label_index_map = {i: options[i] for i in range(num_labels)}
        for item in data:
            if isinstance(item["target"], list):
                if map_target:
                    target_label = RESPONSE_MAP[item["target"][0]]
                else:
                    target_label = item["target"][0]
            else:
                if map_target:
                    target_label = RESPONSE_MAP[item["target"]]
                else:
                    target_label = item["target"]

            if isinstance(item["target"], str):
                target_label = target_label.strip()
            if has_diff_labels:
                option_resp = {i: item["filtered_resps"][i][0] for i in range(len(item["arguments"]))}
                arguments = [quest[1].strip() for quest in item["arguments"]]
                if target_label in arguments:
                    target_label = arguments.index(target_label)

            else:

                option_resp = {
                    item["arguments"][i][1]: item["filtered_resps"][i][0] for i in range(len(item["arguments"]))
                }
            if len(option_resp) < len(options):

                log_likelihoods = [option_resp[option] for option in options[: len(option_resp)]]
                log_likelihoods = np.array(log_likelihoods + [0] * (len(options) - len(option_resp))).reshape(1, -1)

            else:

                log_likelihoods = np.array([option_resp[option] for option in options]).reshape(1, -1)

            probs = softmax(log_likelihoods, axis=1)
            predicted_probabilities.append(probs)
            labels.append(target_label)

    return predicted_probabilities, labels, num_labels, class_label_index_map


def generate_metrics_by_threshold(
    prediction_probabilities, labels, num_labels, label_index_map, metric_by_threshold_path=None
):
    """Generates a CSV file containing metrics by threshold dataframe.

    Parameters:
    prediction_probabilities (array-like): Predicted probabilities for each label.
    labels (array-like): True labels for the data.
    num_labels (int): Number of distinct labels.
    label_index_map (dict): Mapping from labels to label indices.
    metric_by_threshold_path (str, optional): Path to save the metrics CSV file. Defaults to './metric_by_threshold.csv'.

    Return:
    metric_by_threshold (Dataframe): Dataframe with performance metrics at a variable threshold, ranging from 0 to 1.
    """

    if isinstance(labels[0], str) and label_index_map != {}:
        index_label_map = {v.strip() if isinstance(v, str) else v: k for k, v in label_index_map.items()}

        filtered_data = [
            (index_label_map[label.strip()], prob)
            for label, prob in zip(labels, prediction_probabilities)
            if label.strip() in index_label_map
        ]
        labels, prediction_probabilities = zip(*filtered_data)

    prob_thresholds = np.linspace(0, 1, 1001)
    metrics_by_threshold = pd.DataFrame()

    if num_labels == 2:
        # Calculate metrics by threshold for binary label tasks

        metrics_dict = {
            "threshold": prob_thresholds,
            "precision": [
                precision_score(labels, prediction_probabilities > theta, zero_division=0) for theta in prob_thresholds
            ],
            "recall": [
                recall_score(labels, prediction_probabilities > theta, zero_division=0) for theta in prob_thresholds
            ],
            "f1": [f1_score(labels, prediction_probabilities > theta, zero_division=0) for theta in prob_thresholds],
            "accuracy": [accuracy_score(labels, prediction_probabilities > theta) for theta in prob_thresholds],
        }
        metrics_by_threshold = pd.DataFrame.from_dict(metrics_dict)

    else:
        # Calculate metrics by threshold for tasks having multiple distinct labels

        for label_index in range(num_labels):
            prediction_probabilities = np.vstack(prediction_probabilities)
            predicted_probabilities_per_label = prediction_probabilities[:, label_index]
            binary_labels = [1 if label == label_index else 0 for label in labels]
            metrics_dict_per_label = {
                "threshold": prob_thresholds,
                "precision": [
                    precision_score(binary_labels, predicted_probabilities_per_label > theta, zero_division=0)
                    for theta in prob_thresholds
                ],
                "recall": [
                    recall_score(binary_labels, predicted_probabilities_per_label > theta) for theta in prob_thresholds
                ],
                "f1": [f1_score(binary_labels, predicted_probabilities_per_label > theta) for theta in prob_thresholds],
                "accuracy": [
                    accuracy_score(binary_labels, predicted_probabilities_per_label > theta)
                    for theta in prob_thresholds
                ],
                "label": [label_index_map[label_index]] * len(prob_thresholds),
            }
            metrics_by_threshold = pd.concat(
                [metrics_by_threshold, pd.DataFrame.from_dict(metrics_dict_per_label)], ignore_index=True
            )

    if not metric_by_threshold_path:
        metric_by_threshold_path = "./metric_by_threshold.csv"
    else:
        if os.path.exists(metric_by_threshold_path):
            metric_by_threshold_path = os.path.join(metric_by_threshold_path, "metric_by_threshold.csv")

    # Save the DataFrame to the specified path
    metrics_by_threshold.to_csv(metric_by_threshold_path, index=False)

    return metrics_by_threshold
