# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# setup.py

from setuptools import find_packages, setup

setup(
    name="stresscli",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "click",
    ],
    entry_points={
        "console_scripts": [
            "stresscli=commands.main:cli",
        ],
    },
    include_package_data=True,
    description="A CLI tool for dumping test specs and performing load tests.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/intel-sandbox/cloud.performance.benchmark.OPEAStress",  # Update with your actual GitHub URL
    author="Cloud Native Benchmark",
    author_email="your.email@example.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
