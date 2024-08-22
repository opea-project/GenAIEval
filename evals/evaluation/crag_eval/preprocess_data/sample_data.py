import json
import pandas as pd
import os
import argparse
import tqdm

def sample_data(input_file, output_file):
    df = pd.read_json(input_file, lines=True, convert_dates=False)
    # group by `question_type` and `static_or_dynamic`
    df_grouped = df.groupby(['question_type', 'static_or_dynamic'])
    # sample 5 rows from each group if there are more than 5 rows else return all rows
    df_sampled = df_grouped.apply(lambda x: x.sample(5) if len(x) > 5 else x)
    # save sampled data to output file
    df_sampled.to_json(output_file, orient='records', lines=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filedir', type=str, default=None)
    
    args = parser.parse_args()

    data_files = os.listdir(args.filedir)
    for file in tqdm.tqdm(data_files):
        file = os.path.join(args.filedir, file)
        output_file = file.replace('.jsonl', '_sampled.jsonl')
        sample_data(file, output_file)