FILEDIR=$WORKDIR/datasets/crag_task_3_dev_v4
DOCOUT=$WORKDIR/datasets/crag_docs
QAOUT=$WORKDIR/datasets/crag_qas

python process_data.py --data_dir $FILEDIR --docout $DOCOUT --qaout $QAOUT