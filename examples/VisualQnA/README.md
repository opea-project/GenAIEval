# VisualQnA Accuracy Evaluation

## Data preparation

Following [LLaVA's instructions](https://github.com/haotian-liu/LLaVA/blob/main/docs/Evaluation.md). **You MUST first download [eval.zip](https://drive.google.com/file/d/1atZSBBrAX54yYpxtVVW33zFvcnaHeFPy/view?usp=sharing)**. It contains custom annotations, scripts, and the prediction files with LLaVA v1.5. Extract to `vqa_eval`. This also provides a general structure for all datasets.

After downloading all of them, organize the data as follows in `vqa_eval`.

```bash
vqa_eval/
├── gqa
│   ├── answers
│   │   └── llava_gqa_testdev_balanced
│   │       └── llava-v1.5-13b.jsonl
│   ├── data
│   └── llava_gqa_testdev_balanced.jsonl
├── llava-bench-in-the-wild
│   ├── answers
│   │   ├── llava-v1.5-13b.jsonl
│   │   └── llava-v1.5-7b.jsonl
│   └── reviews
│       ├── llava-v1.5-13b-eval1.jsonl
│       ├── llava-v1.5-13b-eval2.jsonl
│       ├── llava-v1.5-13b-eval3.jsonl
│       ├── llava-v1.5-7b-eval1.jsonl
│       ├── llava-v1.5-7b-eval2.jsonl
│       └── llava-v1.5-7b-eval3.jsonl
├── mmbench
│   ├── answers
│   │   └── mmbench_dev_20230712
│   │       └── llava-v1.5-13b.jsonl
│   └── answers_upload
│       └── mmbench_dev_20230712
│           └── llava-v1.5-13b.xlsx
├── MME
│   ├── answers
│   │   └── llava-v1.5-13b.jsonl
│   ├── convert_answer_to_mme.py
│   └── llava_mme.jsonl
├── mm-vet
│   ├── answers
│   │   ├── llava-v1.5-13b.jsonl
│   │   └── llava-v1.5-7b.jsonl
│   ├── convert_answers.py
│   ├── llava-mm-vet.jsonl
│   └── results
│       ├── llava-v1.5-13b_gpt-4-cap-int-score-1runs.csv
│       ├── llava-v1.5-13b_gpt-4-cap-int-score-3runs.csv
│       ├── llava-v1.5-13b_gpt-4-cap-score-1runs.csv
│       ├── llava-v1.5-13b_gpt-4-cap-score-3runs.csv
│       ├── llava-v1.5-13b_gpt-4-grade-1runs.json
│       ├── llava-v1.5-13b_gpt-4-grade-3runs.json
│       ├── llava-v1.5-13b.json
│       ├── llava-v1.5-7b_gpt-4-cap-int-score-1runs.csv
│       ├── llava-v1.5-7b_gpt-4-cap-int-score-3runs.csv
│       ├── llava-v1.5-7b_gpt-4-cap-score-1runs.csv
│       ├── llava-v1.5-7b_gpt-4-cap-score-3runs.csv
│       ├── llava-v1.5-7b_gpt-4-grade-1runs.json
│       ├── llava-v1.5-7b_gpt-4-grade-3runs.json
│       └── llava-v1.5-7b.json
├── pope
│   ├── answers
│   │   └── llava-v1.5-13b.jsonl
│   └── llava_pope_test.jsonl
├── scienceqa
│   ├── answers
│   │   ├── llava-v1.5-13b.jsonl
│   │   ├── llava-v1.5-13b_output.jsonl
│   │   └── llava-v1.5-13b_result.json
│   └── llava_test_CQM-A.json
├── seed_bench
│   ├── answers
│   │   └── llava-v1.5-13b
│   │       └── merge.jsonl
│   ├── answers_upload
│   │   └── llava-v1.5-13b.jsonl
│   ├── extract_video_frames.py
│   └── llava-seed-bench.jsonl
├── textvqa
│   ├── answers
│   │   └── llava-v1.5-13b.jsonl
│   └── llava_textvqa_val_v051_ocr.jsonl
├── vizwiz
│   ├── answers
│   │   └── llava-v1.5-13b.jsonl
│   ├── answers_upload
│   │   └── llava-v1.5-13b.json
│   ├── llava_test.jsonl
│   ├── test
│   ├── test.json
└── vqav2
    ├── answers
    │   └── llava_vqav2_mscoco_test-dev2015
    │       └── llava-v1.5-13b
    │           └── merge.jsonl
    ├── answers_upload
    │   └── llava_vqav2_mscoco_test-dev2015
    │       └── llava-v1.5-13b.json
    ├── llava_vqav2_mscoco_test2015.jsonl
    ├── llava_vqav2_mscoco_test-dev2015.jsonl
    └── test2015
```

## Evaluate VisualQnA

Our evaluation code comes from [LLaVA project](https://github.com/haotian-liu/LLaVA), thanks for their contribution!

### Launch VisualQnA Service
Please refer to [VisualQnA](https://github.com/opea-project/GenAIExamples/blob/main/VisualQnA/README.md) to deploy VisualQnA Service.


Use cURL command to test VisualQnA service and ensure that it has started properly.
```bash
curl http://${host_ip}:80/v1/visualqna -H "Content-Type: application/json" -d '{
     "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What'\''s in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://www.ilankelman.org/stopsigns/australia.jpg"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
    }'
```

### Generation and Evaluation

#### VQAv2

1. Download [`test2015`](http://images.cocodataset.org/zips/test2015.zip) and put it under `vqa_eval/vqav2`.
2. Inference.

```bash
bash scripts/vqav2.sh
```

3. Submit the results to the [evaluation server](https://eval.ai/web/challenges/challenge-page/830/my-submission): `vqa_eval/vqav2/answers_upload`.


#### GQA

1. Download the data following the official instructions [here](https://cs.stanford.edu/people/dorarad/gqa/download.html) and put under `vqa_eval/gqa/data`.
2. Inference.


```bash
bash scripts/gqa.sh
```

#### VisWiz

1. Download [`test.json`](https://vizwiz.cs.colorado.edu/VizWiz_final/vqa_data/Annotations.zip) and extract [`test.zip`](https://vizwiz.cs.colorado.edu/VizWiz_final/images/test.zip) to `test`. Put them under `vqa_eval/vizwiz`.
2. inference.

```bash
bash scripts/vizwiz.sh
```

3. Submit the results to the [evaluation server](https://eval.ai/web/challenges/challenge-page/1911/my-submission): `vqa_eval/vizwiz/answers_upload`.


#### ScienceQA

1. Under `vqa_eval/scienceqa`, download `images`, `pid_splits.json`, `problems.json` from the `data/scienceqa` folder of the ScienceQA [repo](https://github.com/lupantech/ScienceQA).
2. inference.

```bash
bash scripts/sqa.sh
```

#### TextVQA

1. Download [`TextVQA_0.5.1_val.json`](https://dl.fbaipublicfiles.com/textvqa/data/TextVQA_0.5.1_val.json) and [images](https://dl.fbaipublicfiles.com/textvqa/images/train_val_images.zip) and extract to `eval/textvqa`.
2. inference and evaluate.

```bash
bash scripts/textvqa.sh
```

#### POPE

1. Download `coco` from [POPE](https://github.com/AoiDragon/POPE/tree/e3e39262c85a6a83f26cf5094022a782cb0df58d/output/coco) and put under `vqa_eval/pope`.
2. inference and evaluate.


```bash
bash scripts/pope.sh
```

#### MME
1. Download the data following the official instructions [here](https://github.com/BradyFU/Awesome-Multimodal-Large-Language-Models/tree/Evaluation).
2. Downloaded images to `MME_Benchmark_release_version`.
3. Put the official `eval_tool` and `MME_Benchmark_release_version` under `vqa_eval/MME`.
4. inference and evaluate.

```bash
bash scripts/mme.sh
```

#### MMBench

1. Download [`mmbench_dev_20230712.tsv`](https://download.openmmlab.com/mmclassification/datasets/mmbench/mmbench_dev_20230712.tsv) and put under `vqa_eval/mmbench`.
2. inference and evaluate.

```bash
bash scripts/mmbench.sh
```

3. Submit the results to the [evaluation server](https://opencompass.org.cn/leaderboard-multimodal): `vqa_eval/mmbench/answers_upload/mmbench_dev_20230712`.


#### MMBench-CN

1. Download [`mmbench_dev_cn_20231003.tsv`](https://download.openmmlab.com/mmclassification/datasets/mmbench/mmbench_dev_cn_20231003.tsv) and put under `vqa_eval/mmbench`.
2. inference and evaluate.

```bash
bash scripts/mmbench_cn.sh
```

3. Submit the results to the [evaluation server](https://opencompass.org.cn/leaderboard-multimodal): `vqa_eval/mmbench/answers_upload/mmbench_dev_cn_20231003`.


#### SEED-Bench

1. Following the official [instructions](https://github.com/AILab-CVC/SEED-Bench/blob/main/DATASET.md) to download the images and the videos. Put images under `vqa_eval/seed_bench/SEED-Bench-image`.
2. Extract the video frame in the middle from the downloaded videos, and put them under `vqa_eval/seed_bench/SEED-Bench-video-image`.
3. inference and evaluate.

```bash
bash scripts/seed.sh
```

4. Optionally, submit the results to the leaderboard: `vqa_eval/seed_bench/answers_upload` using the official jupyter notebook.


#### LLaVA-Bench-in-the-Wild

1. Extract contents of [`llava-bench-in-the-wild`](https://huggingface.co/datasets/liuhaotian/llava-bench-in-the-wild) to `vqa_eval/llava-bench-in-the-wild`.
2. inference and evaluate.

```bash
bash scripts/llavabench.sh
```


#### MM-Vet

1. Extract [`mm-vet.zip`](https://github.com/yuweihao/MM-Vet/releases/download/v1/mm-vet.zip) to `vqa_eval/mmvet`.
2. inference and evaluate

```bash
bash scripts/mmvet.sh
```


### Accuracy Result
