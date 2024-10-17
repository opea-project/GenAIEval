# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import jsonlines
from datasets import Dataset, load_dataset


class RAGDataset:
    """Dataset class to store data in HF datasets API format."""

    def __init__(self, dataset, field_map, mode, examples):
        self.dataset = dataset
        self.field_map = field_map
        assert mode in ["unit", "local", "benchmarking"], "mode can be either unit or local or benchmarking"
        self.mode = mode
        self.data = self.load_data(examples)
        self.validate_dataset()

    def load_example(self, obj):
        ex = {}
        for out_field, in_field in self.field_map.items():
            if type(obj[in_field]) == list:
                ex[out_field] = "\n".join(obj[in_field])
            else:
                ex[out_field] = obj[in_field]
        return ex

    def load_local_data(self):
        assert os.path.exists(self.dataset), "There is no such file - {}".format(self.dataset)
        with jsonlines.open(self.dataset) as reader:
            data = [self.load_example(obj) for obj in reader]
        return Dataset.from_list(data)

    def load_unit_data(self, examples):
        assert len(examples) >= 1, "Please provide at least one example"
        data = [self.load_example(obj) for obj in examples]
        return Dataset.from_list(data)

    def load_benchmarking_data(self):
        dataset = load_dataset(self.dataset)["train"]
        data = [self.load_example(obj) for obj in dataset]
        return Dataset.from_list(data)

    def load_data(self, examples):
        if self.mode == "local":
            return self.load_local_data()
        elif self.mode == "unit":
            return self.load_unit_data(examples)
        else:
            return self.load_benchmarking_data()

    def validate_dataset(self):
        for i, example in enumerate(self.data):
            for out_field in self.field_map:
                assert out_field in example, "Example {} does not have {} field".format(i + 1, out_field)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)
