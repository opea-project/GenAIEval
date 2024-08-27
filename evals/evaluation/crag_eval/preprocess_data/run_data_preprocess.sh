# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FILEDIR=$WORKDIR/datasets/crag_task_3_dev_v4
DOCOUT=$WORKDIR/datasets/crag_docs
QAOUT=$WORKDIR/datasets/crag_qas

python3 process_data.py --data_dir $FILEDIR --docout $DOCOUT --qaout $QAOUT
