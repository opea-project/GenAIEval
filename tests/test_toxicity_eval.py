# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest

import transformers

from evals.evaluation.toxicity_eval.benchmark_classification_metrics import (
    load_model,
    read_test_jigsaw_split,
    read_test_tc_split,
)


class TestToxicityEval(unittest.TestCase):
    def test_tc_dataset_loading(self):
        csv_path = "hf://datasets/lmsys/toxic-chat/data/0124/toxic-chat_annotation_test.csv"
        assert read_test_tc_split(csv_path)
        self.assertTrue(isinstance(read_test_tc_split(csv_path), tuple))
        self.assertTrue(isinstance(read_test_tc_split(csv_path)[0], list))

    def test_dataset_loading(self):
        csv_path = "dummy_path"
        error_msg = "Error loading test dataset for Jigsaw Unintended Bias."

        with self.assertRaises(Exception) as context:
            read_test_jigsaw_split(csv_path)
        self.assertTrue(error_msg in str(context.exception))

    def test_model_loading(self):
        valid_path = "Intel/toxic-prompt-roberta"
        invalid_path = "dummy_model_path"
        error_msg = "Please make sure that a valid model path is provided."

        assert load_model(valid_path)
        self.assertTrue(
            isinstance(
                load_model(valid_path)[0], transformers.models.roberta.modeling_roberta.RobertaForSequenceClassification
            )
        )

        with self.assertRaises(Exception) as context:
            load_model(invalid_path)
        self.assertTrue(error_msg in str(context.exception))


if __name__ == "__main__":
    unittest.main()
