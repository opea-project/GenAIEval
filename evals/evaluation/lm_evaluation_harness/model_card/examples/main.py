# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os

from evals.evaluation.lm_evaluation_harness.model_card.arguments import parse_arguments
from evals.evaluation.lm_evaluation_harness.model_card.generate_model_card import generate_model_card
from evals.evaluation.lm_evaluation_harness.model_card.utils import generate_metrics_by_threshold, generate_pred_prob


def main():
    args = parse_arguments()
    metric_results_path = args.metric_results_path
    output_dir = args.output_dir
    metrics_by_threshold = args.metrics_by_threshold
    # Generate the metrics by threshold for the metric results if provided by the user

    if metric_results_path:
        if not os.path.exists(args.metric_results_path):
            raise FileNotFoundError(
                f"The file at {metric_results_path} does not exist. Please provide a valid file path."
            )

        try:
            y_pred_prob, labels, num_options, class_label_index_map = generate_pred_prob(metric_results_path)
            metrics_by_threshold = generate_metrics_by_threshold(
                y_pred_prob, labels, num_options, class_label_index_map, output_dir
            )
        except OSError as e:
            print(f"Error: {e}")
        except Exception:
            print("Task is currently not supported for metrics by threshold generation.")
            return

    # Generate the model card
    model_card = generate_model_card(
        args.model_card_json_path,
        metrics_by_threshold,
        args.metrics_by_group,
        mc_template_type=args.mc_template_type,
        output_dir=output_dir,
    )
    return model_card


if __name__ == "__main__":
    main()
