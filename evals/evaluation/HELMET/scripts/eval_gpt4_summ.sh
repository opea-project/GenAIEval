# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

for i in {0..15}; do python scripts/eval_gpt4_summ.py --num_shards 16 --shard_idx $i & done
