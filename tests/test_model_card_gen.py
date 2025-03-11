# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import pkgutil
import unittest

import pandas as pd
from intel_ai_safety.model_card_gen.model_card_gen import ModelCardGen
from intel_ai_safety.model_card_gen.validation import (
    _LATEST_SCHEMA_VERSION,
    _SCHEMA_FILE_NAME,
    _find_json_schema,
    validate_json_schema,
)

PACKAGE = "intel_ai_safety.model_card_gen"

model_card_example = {
    "schema_version": "0.0.1",
    "model_details": {
        "name": "dolore",
        "path": "elit do incididunt",
        "version": {"name": "adipisicing", "diff": "sit pariatur ex Lorem dolore", "date": "2011-03-31"},
        "overview": "amet qui non dolor",
        "documentation": "ut",
    },
}

metrics_by_threshold = pd.DataFrame(
    [
        {"threshold": 0.0, "precision": 0.5, "recall": 1.0, "f1": 0.6, "accuracy": 0.5},
        {"threshold": 0.1, "precision": 0.4, "recall": 0.5, "f1": 0.5, "accuracy": 0.5},
        {"threshold": 0.2, "precision": 0.4, "recall": 0.5, "f1": 0.5, "accuracy": 0.5},
        {"threshold": 0.3, "precision": 0.4, "recall": 0.5, "f1": 0.5, "accuracy": 0.5},
    ]
)

metrics_by_group = pd.DataFrame(
    [
        {"feature": "sex_Female", "group": 0.0, "binary_accuracy": 0.8, "auc": 0.9},
        {"feature": "Overall", "group": "Overall", "binary_accuracy": 0.8, "auc": 0.9},
        {"feature": "sex_Female", "group": 1.0, "binary_accuracy": 0.9, "auc": 0.9},
    ]
)


class TestModelCardGen(unittest.TestCase):

    def test_init(self):
        """Test ModelCardGen initialization."""
        mcg = ModelCardGen(model_card=model_card_example)
        self.assertIsNotNone(mcg.model_card)

    def test_read_json(self):
        """Test ModelCardGen._read_json method."""
        mcg = ModelCardGen(model_card=model_card_example)
        self.assertEqual(mcg.model_card, ModelCardGen._read_json(model_card_example))

    def test_validate_json(self):
        """Test JSON validates."""
        self.assertEqual(validate_json_schema(model_card_example), _find_json_schema())

    def test_schemas(self):
        """Test JSON schema loads."""
        schema_file = os.path.join("schema", "v" + _LATEST_SCHEMA_VERSION, _SCHEMA_FILE_NAME)
        json_file = pkgutil.get_data(PACKAGE, schema_file)
        schema = json.loads(json_file)
        self.assertEqual(schema, _find_json_schema(_LATEST_SCHEMA_VERSION))

    def test_load_from_csv(self):
        """Test if metrics files are loaded properly and generate model card."""
        mcg = ModelCardGen.generate(metrics_by_threshold=metrics_by_threshold, metrics_by_group=metrics_by_group)
        self.assertIsNotNone(mcg.model_card)

    def test_load_template(self):
        """Test ModelCardGen generates a model card using the specified template type."""
        for template_type in ("md", "html"):
            with self.subTest(template_type=template_type):
                mcg = ModelCardGen.generate(template_type=template_type)
                self.assertIsNotNone(mcg.model_card)

    def test_missing_threshold_column_exception(self):
        """Test if the correct exception is raised when the 'threshold' column is missing in the CSV."""
        with self.assertRaises(AssertionError) as context:
            example_df = pd.DataFrame(data={"col1": [1, 2]})
            ModelCardGen.generate(metrics_by_threshold=example_df)
        self.assertTrue("No column named 'threshold'" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
