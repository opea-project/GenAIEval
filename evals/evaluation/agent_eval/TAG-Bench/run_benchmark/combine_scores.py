import pandas as pd
import os
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--filedir', type=str, required=True, help='Directory containing the csv files')
args = parser.parse_args()

filedir = args.filedir
csv_files = glob.glob(os.path.join(filedir, '*_graded.csv'))
print("Number of score files found: ", len(csv_files))
print(csv_files)

df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

print("Average score of all questions: ", df["answer_correctness"].mean())
