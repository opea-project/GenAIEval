#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re

from setuptools import find_packages, setup

try:
    filepath = "./evals/version.py"
    with open(filepath) as version_file:
        (__version__,) = re.findall('__version__ = "(.*)"', version_file.read())
except Exception as error:
    assert False, "Error: Could not open '%s' due %s\n" % (filepath, error)

setup(
    name="opea-eval",
    version=__version__,
    author="Intel AISE AIPC Team",
    author_email="haihao.shen@intel.com, feng.tian@intel.com, chang1.wang@intel.com, kaokao.lv@intel.com",
    description="Evaluation and benchmark for Generative AI",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/opea-project/GenAIEval",
    packages=find_packages(),
    package_data={"evals.benchmark.stresscli.locust": ["*.conf"], "evals/benchmark/stresscli/commands": ["config.ini"]},
    python_requires=">=3.10",
)
