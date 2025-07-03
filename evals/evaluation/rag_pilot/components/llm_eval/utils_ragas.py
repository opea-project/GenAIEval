from ragas import metrics
from .metrics import *

RAGAS_METRIC_FUNC_MAP = {
    context_recall: metrics.context_recall,
    context_precision: metrics.context_precision,
    context_entity_recall: metrics.context_entity_recall,
    answer_correctness: metrics.answer_correctness,
    answer_relevancy: metrics.answer_relevancy,
    answer_similarity: metrics.answer_similarity,
    faithfulness: metrics.faithfulness,
}
