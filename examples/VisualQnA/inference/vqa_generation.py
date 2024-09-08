# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import requests
import os
import json
from tqdm import tqdm
import shortuuid

from PIL import Image
import math


def split_list(lst, n):
    """Split a list into n (roughly) equal-sized chunks"""
    chunk_size = math.ceil(len(lst) / n)  # integer division
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]


def get_chunk(lst, n, k):
    chunks = split_list(lst, n)
    return chunks[k]


def eval_model(args):
    questions = [json.loads(q) for q in open(os.path.expanduser(args.question_file), "r")]
    questions = get_chunk(questions, args.num_chunks, args.chunk_idx)
    answers_file = os.path.expanduser(args.answers_file)
    os.makedirs(os.path.dirname(answers_file), exist_ok=True)
    ans_file = open(answers_file, "w")

    cnt = -1
    for line in tqdm(questions, total=len(questions)):
        cnt += 1
        idx = line["question_id"]
        cur_prompt = line["text"]
        image_file = line["image"]
        
        # Construct the payload for the HTTP request
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": cur_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"http://{args.image_folder}/{image_file}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": args.max_new_tokens
        }

        # Send the HTTP request to the VisualQnA service
        response = requests.post(f"http://{args.host_ip}:8888/v1/visualqna",
                                 headers={"Content-Type": "application/json"},
                                 json=payload)

        if response.status_code == 200:
            outputs = response.json()['choices'][0]['message']['content']
        else:
            print(f"Failed to get response from VisualQnA service: {response.status_code}")
            outputs = "Error in response"

        print(outputs)
        ans_id = shortuuid.uuid()
        ans_file.write(json.dumps({"question_id": idx,
                                   "prompt": cur_prompt,
                                   "text": outputs,
                                   "answer_id": ans_id,
                                   "model_id": "visualqna_service",
                                   "metadata": {}}) + "\n")
    ans_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-folder", type=str, default="")
    parser.add_argument("--question-file", type=str, default="tables/question.jsonl")
    parser.add_argument("--answers-file", type=str, default="answer.jsonl")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=1)
    parser.add_argument("--max_new_tokens", type=int, default=128)
    args = parser.parse_args()

    eval_model(args)

