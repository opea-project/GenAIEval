# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import glob
import os

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--filedir", type=str, required=True, help="Directory containing the csv files")
args = parser.parse_args()

filedir = args.filedir
csv_files = glob.glob(os.path.join(filedir, "*_graded.csv"))
print("Number of score files found: ", len(csv_files))
print(csv_files)

df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
print(df.columns)
print("Average score of all questions: ", df["answer_correctness"].mean())

# average score per csv file
for f in csv_files:
    df = pd.read_csv(f)
    print(f, df["answer_correctness"].mean())
