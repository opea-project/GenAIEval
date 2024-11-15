filedir=$WORKDIR/datasets/crag_results/
conv_rag="conv_rag_graded.csv" # replace with your file name
ragagent="ragagent_graded.csv" # replace with your file name
reactagent="react_graded.csv" # replace with your file name
human_scores_file="human_scores.csv" # replace with your file name

python3 compare_scores.py \
--filedir $filedir \
--conv_rag $conv_rag \
--ragagent $ragagent \
--reactagent $reactagent \
--human_scores_file $human_scores_file