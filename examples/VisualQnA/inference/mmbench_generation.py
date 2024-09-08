
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import json
import pandas as pd
from tqdm import tqdm
import shortuuid
import requests

from PIL import Image
from io import BytesIO
import base64
import math

def load_image_from_base64(image):
    return Image.open(BytesIO(base64.b64decode(image)))

def split_list(lst, n):
    """Split a list into n (roughly) equal-sized chunks"""
    chunk_size = math.ceil(len(lst) / n)  # integer division
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]


def get_chunk(lst, n, k):
    chunks = split_list(lst, n)
    return chunks[k]


def is_none(value):
    if value is None:
        return True
    if type(value) is float and math.isnan(value):
        return True
    if type(value) is str and value.lower() == 'nan':
        return True
    if type(value) is str and value.lower() == 'none':
        return True
    return False

def get_options(row, options):
    parsed_options = []
    for option in options:
        option_value = row[option]
        if is_none(option_value):
            break
        parsed_options.append(option_value)
    return parsed_options

all_options = ['A', 'B', 'C', 'D']

def eval_model(args):
    questions = pd.read_table(os.path.expanduser(args.question_file))
    questions = get_chunk(questions, args.num_chunks, args.chunk_idx)
    answers_file = os.path.expanduser(args.answers_file)
    os.makedirs(os.path.dirname(answers_file), exist_ok=True)
    ans_file = open(answers_file, "w")

    cnt = -1
    for index, row in tqdm(questions.iterrows(), total=len(questions)):
        options = get_options(row, all_options)
        cur_option_char = all_options[:len(options)]

        if args.all_rounds:
            num_rounds = len(options)
        else:
            num_rounds = 1

        for round_idx in range(num_rounds):
            cnt += 1
            idx = row['index']
            question = row['question']
            hint = row['hint']
            image = load_image_from_base64(row['image'])  # Assumes image is base64 encoded
            if not is_none(hint):
                question = hint + '\n' + question
            for option_char, option in zip(all_options[:len(options)], options):
                question = question + '\n' + option_char + '. ' + option

            # Prepare data for the POST request
            payload = {
                "question": question,
                "image": row['image'],  # Assuming image is already base64 encoded
                "options": options
            }

            # Send POST request
            response = requests.post(args.service_url, json=payload)
            if response.status_code == 200:
                outputs = response.json().get('answer', '').strip()
            else:
                print(f"Error: Received status code {response.status_code}")
                outputs = ""

            ans_id = shortuuid.uuid()
            ans_file.write(json.dumps({
                "question_id": idx,
                "round_id": round_idx,
                "prompt": question,
                "text": outputs,
                "options": options,
                "option_char": cur_option_char,
                "answer_id": ans_id,
                "metadata": {}
            }) + "\n")
            ans_file.flush()

            # Rotate options
            options = options[1:] + options[:1]
            cur_option_char = cur_option_char[1:] + cur_option_char[:1]

    ans_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question-file", type=str, default="tables/question.jsonl")
    parser.add_argument("--answers-file", type=str, default="answer.jsonl")
    parser.add_argument("--all-rounds", action="store_true")
    parser.add_argument("--lang", type=str, default="en")
    parser.add_argument("--service-url", type=str, required=True, help="URL of the VisualQnA service")
    args = parser.parse_args()

    eval_model(args)

