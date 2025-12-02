from abc import ABC, abstractmethod
from typing import Any, Optional, List
from enum import Enum
import warnings
import torch

from datasets import Dataset
import numpy as np
import threading

from .doc import RAGResults, RAGResult
from .metrics import *
from .utils_eval import load_hf_pipeline, clean_memory

class EvaluatorType(str, Enum):

    RAGAS = "ragas"
    DEEPEVAL = "deepeval"


class MetricsParser(ABC):

    def __init__(self):
        self.metrics = []

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def create_metrics(self, metrics: List[str]):
        pass

    @abstractmethod
    def evaluate(self, results: RAGResults, metrics=all_metrics, save_path=None):
        pass

    def aggregate_results_metrics(self, results: RAGResults):
        for group, group_metrics in METRIC_GROUP_MAP.items():
            if group == all_metrics:
                continue
            for metric in group_metrics:
                if metric in self.metrics:
                    metric_values = [result.metrics.get(metric, np.nan) for result in results.results]
                    if not np.isnan(metric_values).all():
                        results.metrics[group][metric] = round(np.nanmean(metric_values) * 100, 1)
                    else:
                        results.metrics[group][metric] = np.nan

    def save_results(self, results, save_path):
        if save_path is not None:
            with open(save_path, "w") as f:
                f.write(results.to_json(indent=2))


default_embedding_model_name = "BAAI/bge-small-zh-v1.5"
class RagasMetricsParser(MetricsParser):

    def __init__(self, llm_name, embedding_model_name = default_embedding_model_name):
        super().__init__()

        self.llm_name = llm_name
        self.embedding_model_name = embedding_model_name
        self.llm = None
        self.embedding = None
        self.run_config = None

        self.load_model()

    def load_model(self):
        from langchain_huggingface.llms import HuggingFacePipeline
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from ragas.embeddings.base import LangchainEmbeddingsWrapper
        from ragas import RunConfig

        pipe = load_hf_pipeline(self.llm_name)
        self.llm = HuggingFacePipeline(pipeline=pipe)
        self.embedding = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
            encode_kwargs={"normalize_embeddings": True},  # Normalize for cosine similarity
            ))
        self.run_config = RunConfig(timeout=12000)

    def create_metrics(self, eval_metrics: List[str]):
        from .utils_ragas import RAGAS_METRIC_FUNC_MAP
        if isinstance(eval_metrics, str):
            eval_metrics = [eval_metrics]

        ret_metrics = set()
        for metric in eval_metrics:
            if metric not in RAGAS_METRIC_FUNC_MAP:
                if metric not in METRIC_GROUP_MAP:
                    warnings.warn(f"Invalid metric: {metric}.")
                else:
                    ret_metrics.update(METRIC_GROUP_MAP[metric])
            else:
                ret_metrics.add(metric)

        metrics_func = []
        for metric in ret_metrics:
            if metric in RAGAS_METRIC_FUNC_MAP:
                metrics_func.append(RAGAS_METRIC_FUNC_MAP[metric])

        self.metrics_func = metrics_func
        self.metrics = ret_metrics

    def results2datasets(self, results: RAGResults):
        data_collections = {
            "question": [result.query for result in results.results],
            "answer": [result.response for result in results.results],
            "ground_truth": [result.gt_answer if result.gt_answer else "" for result in results.results] ,
            "contexts": [[doc.text for doc in result.retrieved_contexts] if result.retrieved_contexts else [""] for result in results.results ],
        }

        return Dataset.from_dict(data_collections)

    def evaluate(self, results: RAGResults, save_path=None):
        from ragas import evaluate
        from .utils_ragas import RAGAS_METRIC_FUNC_MAP

        dataset = self.results2datasets(results)
        scores = evaluate(
            dataset=dataset,
            metrics=self.metrics_func,
            llm=self.llm,
            embeddings=self.embedding,
            raise_exceptions=False,
            run_config=self.run_config
        )
        df = scores.to_pandas()
        for metric in self.metrics:
            if metric in RAGAS_METRIC_FUNC_MAP:
                for result, metric_value in zip(results.results, df[metric]):
                    if not (np.isnan(metric_value) and metric in result.metrics):
                        result.metrics[metric] = metric_value
                    print(f"result {result.query_id} metrics[{metric}]={metric_value}")

        self.aggregate_results_metrics(results)
        self.save_results(results, save_path)

        return results.metrics

    
class DeepevalMetricsParser(MetricsParser):

    def __init__(self, llm_name):
        super().__init__()

        self.llm_name = llm_name
        self.llm = None

        self.load_model()

    def load_model(self):
        from .utils_deepeval import DeepEvalCustomEvalLLM
        self.llm = DeepEvalCustomEvalLLM(self.llm_name)

    def create_metrics(self, eval_metrics: List[str]):
        from .utils_deepeval import DEEPEVAL_METRIC_FUNC_MAP
        if isinstance(eval_metrics, str):
            eval_metrics = [eval_metrics]

        llm = self.llm
        ret_metrics = set()
        for metric in eval_metrics:
            if metric not in DEEPEVAL_METRIC_FUNC_MAP:
                if metric not in METRIC_GROUP_MAP:
                    warnings.warn(f"Invalid metric: {metric}.")
                else:
                    ret_metrics.update(METRIC_GROUP_MAP[metric])
            else:
                ret_metrics.add(metric)

        metrics_func = {}
        for metric in ret_metrics:
            if metric in DEEPEVAL_METRIC_FUNC_MAP:
                #metric_instance = DEEPEVAL_METRIC_FUNC_MAP[metric](model=llm)
                metric_instance = DEEPEVAL_METRIC_FUNC_MAP[metric](model=llm, include_reason = False) #TODO Test
                metrics_func[metric] = metric_instance

        self.metrics_func = metrics_func
        self.metrics = ret_metrics

    def result2dataset(self, result: RAGResult):
        from deepeval.test_case import LLMTestCase
        test_case = LLMTestCase(
            input=result.query,
            actual_output=result.response,
            expected_output=result.gt_answer if result.gt_answer else "",
            retrieval_context=[doc.text for doc in result.retrieved_contexts] if result.retrieved_contexts else [""],
            # context=["The chicken wanted to cross the road."] list of strings, GT for context
        )

        return test_case

    def evaluate(self, results: RAGResults, save_path=None):
        for result in results.results:
            test_case = self.result2dataset(result)
            print(f"Evaluating test case {result.query_id}")
            for metric, metric_func in self.metrics_func.items():
                if metric not in result.metrics:
                    clean_memory()
                    def evaluate_metric():
                        metric_func.measure(test_case)
                        result.metrics[metric] = metric_func.score
                        print(f"result {result.query_id} metrics[{metric}]={metric_func.score}")
                        self.save_results(results, save_path)
                    
                    evaluation_thread = threading.Thread(target=evaluate_metric)
                    evaluation_thread.start()
                    evaluation_thread.join()
        
        self.aggregate_results_metrics(results)
        self.save_results(results, save_path)

        return results.metrics
