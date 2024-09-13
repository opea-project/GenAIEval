
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

python ../../evaluation/rag_eval/examples/eval_crud.py --dataset_path data/split_merged.json --docs_path data/80000_docs --ingest_docs --chunk_size $1 --chunk_overlap $2 --service_url $3 --database_endpoint $4 --embedding_endpoint $5 --retrieval_endpoint $6
