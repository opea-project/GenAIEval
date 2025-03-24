# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a model card with optional metrics processing.")
    parser.add_argument("--input_mc_metadata_json", type=str, required=True, help="Path to the JSON file containing input model card metadata.")
    parser.add_argument(
        "--metrics_by_threshold",
        type=str,
        default=None,
        help="Metrics by threshold dataframe or the path to the metrics by threshold CSV file.",
    )
    parser.add_argument(
        "--metrics_by_group",
        type=str,
        default=None,
        help="Metrics by group dataframe or Path to the metrics by group CSV file.",
    )
    parser.add_argument(
        "--metric_results_path",
        type=str,
        default=None,
        help="Path to the metric results JSONL file for which metrics by threshold dataframe needs to be generated.",
    )
    parser.add_argument(
        "--mc_template_type",
        type=str,
        default="html",
        help="Template to use for rendering the model card. html for an interactive HTML model card or md for a static Markdown version. Defaults to html",
    )
    parser.add_argument(
        "--output_dir", type=str, default=None, help="Directory to save the generated model card and related files."
    )
    args = parser.parse_args()

    return args