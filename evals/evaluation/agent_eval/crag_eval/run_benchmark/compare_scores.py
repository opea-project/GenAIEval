import pandas as pd
from scipy.stats import spearmanr, pearsonr


def merge_and_get_stats(filedir, conv_rag, ragagent, reactagent, prefix=""):
    conv_rag_df = pd.read_csv(filedir+conv_rag)
    ragagent_df = pd.read_csv(filedir+ragagent)
    reactagent_df = pd.read_csv(filedir+reactagent)

    conv_rag_df = conv_rag_df.rename(columns={"answer_correctness": "conv_rag_score"})
    ragagent_df = ragagent_df.rename(columns={"answer_correctness": "ragagent_score"})
    reactagent_df = reactagent_df.rename(columns={"answer_correctness": "reactagent_score"})
    merged_df = pd.merge(conv_rag_df, ragagent_df, on="query")
    merged_df = pd.merge(merged_df, reactagent_df, on="query")
    print(merged_df.shape)
    merged_df.to_csv(filedir+prefix+"merged_scores.csv", index=False)

    # drop rows with nan
    merged_df_dropped = merged_df.dropna()
    # merged_df = merged_df.reset_index(drop=True)
    print(merged_df_dropped.shape)

    # compare scores
    print(merged_df_dropped.describe())
    merged_df_dropped.to_csv(filedir+prefix+"merged_scores_nadropped.csv", index=False)
    return merged_df, merged_df_dropped



#RAGAS scores
print("===============RAGAS scores==================")
filedir="/localdisk/minminho/dataset/rag_eval/"
conv_rag="rag_llama3.1-70B-instruct_92queries_graded.csv"
ragagent="ragagent_chatopenai_tgi_llama3.1-70B-instruct_92queries_graded.csv"
reactagent="react_v3parser_v3prompt_tgi_chatopenai_llama3.1-70B-instruct_92queries_graded.csv"
merged_df, merged_df_dropped = merge_and_get_stats(filedir, conv_rag, ragagent, reactagent)

# human scores
print("===============Human scores==================")
human_scores = "human_scores_92queries.csv"
human_scores_df = pd.read_csv(filedir+human_scores)
print(human_scores_df.describe())

human_scores_df_dropped = human_scores_df.loc[human_scores_df["query"].isin(merged_df_dropped["query"])]
print(human_scores_df_dropped.describe())
human_scores_df_dropped.to_csv(filedir+"human_scores_dropped.csv", index=False)

# calculate spearman correlation
print("===============Spearman correlation==================")
print(spearmanr(merged_df_dropped["conv_rag_score"], human_scores_df_dropped["conv_rag"]))
print(spearmanr(merged_df_dropped["ragagent_score"], human_scores_df_dropped["ragagent"]))
print(spearmanr(merged_df_dropped["reactagent_score"], human_scores_df_dropped["reactagent"]))

# concat conv_rag, ragagent, reactagent scores in merged_df_dropped
ragas_scores = pd.concat([merged_df_dropped["conv_rag_score"], merged_df_dropped["ragagent_score"], merged_df_dropped["reactagent_score"]], axis=0)
human_scores = pd.concat([human_scores_df_dropped["conv_rag"], human_scores_df_dropped["ragagent"], human_scores_df_dropped["reactagent"]], axis=0)
print(spearmanr(ragas_scores, human_scores))

# pearson correlation
print("===============Pearson correlation==================")
print(pearsonr(merged_df_dropped["conv_rag_score"], human_scores_df_dropped["conv_rag"]))
print(pearsonr(merged_df_dropped["ragagent_score"], human_scores_df_dropped["ragagent"]))
print(pearsonr(merged_df_dropped["reactagent_score"], human_scores_df_dropped["reactagent"]))
print(pearsonr(ragas_scores, human_scores))



