# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse

import pandas as pd
from scipy.stats import pearsonr, spearmanr


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filedir", type=str, help="file directory")
    parser.add_argument("--conv_rag", type=str, help="file with RAGAS scores for conventional RAG")
    parser.add_argument("--ragagent", type=str, help="file with RAGAS scores for RAG agent")
    parser.add_argument("--reactagent", type=str, help="file with RAGAS scores for React agent")
    parser.add_argument("--human_scores_file", type=str, help="file with human scores for 3 setups")
    return parser.parse_args()


def merge_and_get_stats(filedir, conv_rag, ragagent, reactagent, prefix=""):
    conv_rag_df = pd.read_csv(filedir + conv_rag)
    ragagent_df = pd.read_csv(filedir + ragagent)
    reactagent_df = pd.read_csv(filedir + reactagent)

    conv_rag_df = conv_rag_df.rename(columns={"answer_correctness": "conv_rag_score"})
    ragagent_df = ragagent_df.rename(columns={"answer_correctness": "ragagent_score"})
    reactagent_df = reactagent_df.rename(columns={"answer_correctness": "reactagent_score"})
    merged_df = pd.merge(conv_rag_df, ragagent_df, on="query")
    merged_df = pd.merge(merged_df, reactagent_df, on="query")
    print(merged_df.shape)
    print(merged_df.describe())
    merged_df.to_csv(filedir + prefix + "merged_scores.csv", index=False)

    # drop rows with nan
    merged_df_dropped = merged_df.dropna()
    # merged_df = merged_df.reset_index(drop=True)
    print(merged_df_dropped.shape)

    # compare scores
    print(merged_df_dropped.describe())
    merged_df_dropped.to_csv(filedir + prefix + "merged_scores_nadropped.csv", index=False)
    return merged_df, merged_df_dropped


if __name__ == "__main__":
    args = get_args()
    filedir = args.filedir
    conv_rag = args.conv_rag
    ragagent = args.ragagent
    reactagent = args.reactagent
    human_scores_file = args.human_scores_file

    # RAGAS scores
    print("===============RAGAS scores==================")
    merged_df, merged_df_dropped = merge_and_get_stats(filedir, conv_rag, ragagent, reactagent)

    # human scores
    print("===============Human scores==================")
    human_scores_df = pd.read_csv(filedir + human_scores_file)
    print(human_scores_df.describe())

    human_scores_df_dropped = human_scores_df.loc[human_scores_df["query"].isin(merged_df_dropped["query"])]
    print(human_scores_df_dropped.describe())
    human_scores_df_dropped.to_csv(filedir + "human_scores_dropped.csv", index=False)

    # concat conv_rag, ragagent, reactagent scores in merged_df_dropped
    ragas_scores = pd.concat(
        [
            merged_df_dropped["conv_rag_score"],
            merged_df_dropped["ragagent_score"],
            merged_df_dropped["reactagent_score"],
        ],
        axis=0,
    )
    human_scores = pd.concat(
        [
            human_scores_df_dropped["conv_rag"],
            human_scores_df_dropped["ragagent"],
            human_scores_df_dropped["reactagent"],
        ],
        axis=0,
    )

    # calculate spearman correlation
    print("===============Spearman correlation==================")
    print(spearmanr(ragas_scores, human_scores))

    # pearson correlation
    print("===============Pearson correlation==================")
    print(pearsonr(ragas_scores, human_scores))
