#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from scripts.benchmark_classification_metrics import load_model, read_test_tc_split, read_test_jigsaw_split

MODEL_PATHS = ["dummy_model_path", "Intel/toxic-prompt-roberta"]


@pytest.mark.common
@pytest.mark.parametrize(
    ("invalid_model_path", "valid_model_path"), [("dummy_model_path", "Intel/toxic-prompt-roberta")]
)
def test_model_loading(invalid_model_path, valid_model_path):
    """Test Loading of HuggingFace model path"""

    assert load_model(valid_model_path)
    with pytest.raises(EnvironmentError) as exception_error:
        load_model(invalid_model_path)
    assert "Please make sure that a valid model path is provided." in str(exception_error.value)


@pytest.mark.common
def test_dataset_loading():
    csv_path = "dummy_path"
    with pytest.raises(Exception) as exception_error:
        read_test_jigsaw_split(csv_path)
    assert (
        "Error loading test dataset for Jigsaw Unintended Bias. Please ensure the CSV file path is correct and the file contains the required columns: 'comment_text' and 'toxicity'."
        in str(exception_error.value)
    )


@pytest.mark.common
def test_tc_dataset_loading():
    csv_path = "hf://datasets/lmsys/toxic-chat/data/0124/toxic-chat_annotation_test.csv"
    assert read_test_tc_split(csv_path)
