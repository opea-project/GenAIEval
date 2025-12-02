overall_metrics = "overall_metrics"
precision = "precision"
recall = "recall"
f1 = "f1"

retriever_metrics = "retriever_metrics"
context_recall = "context_recall"
context_precision = "context_precision"
context_relevancy = "context_relevancy"
context_entity_recall = "context_entity_recall"

generator_metrics = "generator_metrics"
answer_correctness = "answer_correctness"
answer_relevancy = "answer_relevancy"
answer_similarity = "answer_similarity"
faithfulness = "faithfulness"

all_metrics = "all_metrics"


METRIC_GROUP_MAP = {
    overall_metrics: [precision, recall, f1],
    retriever_metrics: [context_recall, context_precision, context_entity_recall, context_relevancy],
    generator_metrics: [answer_correctness, answer_relevancy, answer_similarity, faithfulness],
    all_metrics: [
        precision, recall, f1,
		context_recall, context_precision, context_entity_recall, context_relevancy,
        answer_correctness, answer_relevancy, answer_similarity, faithfulness
    ]
}
