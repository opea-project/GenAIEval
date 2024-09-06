# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tokenresponse as token


def getUrl():
    return "/v1/reranking"


my_query = "What is Deep Learning?"
query_rerank_1 = """Deep learning is a subset of machine learning, which itself is a branch of artificial intelligence (AI). It involves the use of neural networks with many layers—hence "deep." These networks are capable of learning from data in a way that mimics human cognition to some extent. The key idea is to create a system that can process inputs through multiple layers where each layer learns to transform its input data into a slightly more abstract and composite representation. In a typical deep learning model, the input layer receives the raw data, similar to the way our senses work. This data is then passed through multiple hidden layers, each of which transforms the incoming data using weights that are adjusted during training. These layers might be specialized to recognize certain types of features in the data, like edges or textures in an image, specific words or phrases in a text, or particular frequency patterns in audio. The final layer produces the output of the model, which could be a class label in classification tasks, a continuous value in regression, or a complex pattern in generative models. Deep learning has been behind many of the recent advancements in AI, including speech recognition, image recognition, natural language processing, and autonomous driving."""
query_rerank_2 = """Deep learning is a powerful tool in the field of artificial intelligence, but it's important to recognize what it is not. Deep learning is not a solution to all types of data processing or decision-making problems. While deep learning models excel at tasks involving large amounts of data and complex patterns, they are not as effective for tasks that require reasoning, logic, or understanding of abstract concepts, which are better handled by other types of AI algorithms. Deep learning is also not a synonym for all of machine learning. Traditional machine learning encompasses a broader range of techniques that include not only neural networks but also methods like decision trees, support vector machines, and linear regression. These traditional models often require less data and computational power and can be more interpretable than deep learning models. They are particularly useful in scenarios where the underlying relationships in the data are more straightforward or where transparency in decision-making is critical. Additionally, deep learning is not inherently unbiased or fair. The models can perpetuate or even amplify biases present in the training data, leading to unfair outcomes in applications like hiring, lending, and law enforcement."""


def getReqData():
    return {"initial_query": my_query, "retrieved_docs": [{"text": query_rerank_1}, {"text": query_rerank_2}]}


def respStatics(environment, reqData, resp):
    return {
        "total_latency": resp["total_latency"] * 1000,
    }


def staticsOutput(environment, reqlist):
    token.staticsOutputForMicroservice(environment, reqlist)
