import datetime
import json
import os
import requests
from .metrics import bleu_score, rougeL_score, LLM_score
from tqdm import tqdm

class CRUD_Evaluator:
    def __init__(
        self,
        dataset: list[dict],
        output_path: str,
        task: str,
    ) -> None:
        """Args:
            dataset (list[dict]): The dataset for evaluation.
            output_path (str): The path to save results.
            task (str): Task to evaluate.
        """
        self.task = task
        self.output_path = output_path
        self.dataset = dataset

    @staticmethod
    def ingest_docs(documents_path, database_endpoint):
        files = []
        if os.path.isfile(documents_path):
            files.append(documents_path)
        elif os.path.isdir(documents_path):
            for root, dirs, files_ in os.walk(documents_path):
                files += [os.path.join(root, f) for f in files_]
        for file in files:
            file_obj = open(file, mode='rb')
            response = requests.post(database_endpoint, files={'files':file_obj})
            if response.status_code == 200:
                print(f"Successfully ingested {file}.")
            else:
                print(f"Failed to ingest {file}.")
            file_obj.close()

    def scoring(self, data: dict, llm_endpoint: str=None) -> dict:
        generated_text = data["generated_text"]
        if self.task == "summarization":
            ground_truth_text = data["summary"]
        elif self.task == "question_answering":
            ground_truth_text = data["answers"]
        elif self.task == "continuation":
            ground_truth_text = data["continuing"]
        elif self.task == "hallucinated_modified":
            ground_truth_text = data["hallucinatedMod"]
        else:
            raise NotImplementedError(
                f"Unknown task {self.task}, only support "
                "summarization, question_answering, continuation and hallucinated_modified."
            )
        data["ground_truth_text"] = ground_truth_text

        bleu_avg, bleu1, bleu2, bleu3, bleu4 = bleu_score(generated_text, ground_truth_text)

        return {
            'metrics': {
                'bleu-avg': bleu_avg or 0.0,
                'bleu-1': bleu1 or 0.0,
                'bleu-2': bleu2 or 0.0,
                'bleu-3': bleu3 or 0.0,
                'bleu-4': bleu4 or 0.0,
                'rouge-L': rougeL_score(generated_text, ground_truth_text) or 0.0,
                'LLM-score': LLM_score(generated_text, ground_truth_text, llm_endpoint) or 0.0,
                'length': len(generated_text)
            },
            'log': {
                'generated_text': generated_text,
                'ground_truth_text': ground_truth_text,
                'evaluateDatetime': str(datetime.datetime.now()),
            },
            'valid': len(generated_text.strip()) != 0
        }

    def compute_overall(self, results: list[dict]) -> dict:
        overall = {'bleu-avg': 0, 'bleu-1': 0, 'bleu-2': 0, 'bleu-3': 0, 
                    'bleu-4': 0, 'rouge-L': 0, 'LLM-score': 0.0, 'length': 0}

        for result in results:
            overall = {key: overall[key] + result['metrics'][key] for key in overall.keys()}

        overall_save = {f"avg. {key}": value / len(results) for key, value in overall.items()}

        overall_save['num'] = len(results)
        
        return overall_save


    def save_output(self, output: dict) -> None:
        """Save evaluation results."""
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
    
    def read_output(self) -> dict:
        with open(self.output_path) as f:
            return json.load(f)

    def remove_invalid(self, results: list[dict]) -> list[dict]:
        """Remove invalid results from the list and return the cleaned results."""
        return [result for result in results if result['valid']]

    def get_query_doc_from_data(self, data):
        if self.task == "summarization":
            query = data["text"]
            document = data["text"]
        elif self.task == "question_answering":
            query = data["questions"]
            document = data["news1"]
        elif self.task == "continuation":
            query = data["beginning"]
            document = data["beginning"]
        elif self.task == "hallucinated_modified":
            query = data["newsBeginning"]
            document = data["newsBeginning"]
        else:
            raise NotImplementedError(
                f"Unknown task {self.task}, only support "
                "summarization, question_answering, continuation and hallucinated_modified."
            )
        return query, document

    def send_request(self, data, arguments):
        service_url = arguments.service_url
        headers = {"Content-Type": "application/json"}
        json_data = {}
        query, _ = self.get_query_from_data(data)
        json_data["messages"] = query
        json_data["stream"] = False
        json_data["temperature"] = arguments.temperature
        json_data["max_new_tokens"] = arguments.max_new_tokens
        json_data = json.dumps(json_data)
        response = requests.post(service_url, data=json_data, headers=headers)
        return response.json()["choices"][0]["message"]["content"]

    def get_retrieved_documents(self, data, arguments):
        query, _ = self.get_query_from_data(data)
        data = {"text": query}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(arguments.embedding_endpoint, data=json.dumps(data), headers=headers)
        embedding = resp.json()["embedding"]
        data = {"text": query, "embedding": embedding, "search_typ": "similarity", "k": 4, "fetch_k": 20, "lambda_mult": 0.5}
        resp = requests.post(arguments.retrieval_endpoint, data=json.dumps(data), headers=headers)
        retrieved_documents = resp.json()["retrieved_docs"]
        return [doc["text"] for doc in retrieved_documents]

    def scoring_retrieval(self, data, retrieved_documents):
        _, ground_truth_documents = self.get_query_from_data(data)

    def evaluate(self, arguments, sort=True, show_progress_bar=False, contain_original_data=False):
        """Run a complete evaluation.
        
        Args:
            dataset (list[dict]): The dataset for evaluation.
            output_path (str): The path to save results.
            task (str): Task to evaluate.
            arguments: Arguments.
            sort (bool): Whether to sort the results by id.
            show_progress_bar (bool): Whether to display a progress bar.
            contain_original_data (bool): Whether to include original data in the results for debugging.
        
        Returns:
            dict: Output dictionary contains fields such as: overall, results, etc.
        """
        if os.path.exists(self.output_path):  # Resume evaluation
            results = self.read_output().get('results', [])
            results = self.remove_invalid(results)
            saved_ids = [result['id'] for result in results]
        else:
            results = []
            saved_ids = []

        for data in (tqdm(self.dataset) if show_progress_bar else self.dataset):
            if data['ID'] in saved_ids:
                continue  # Skip results that have already been evaluated and are valid
            try:
                retrieved_documents = self.get_retrieved_documents(data, arguments)
                data["retrieved_documents"] = retrieved_documents
                generated_text = self.send_request(data, arguments)
                data["generated_text"] = generated_text
                result = {'id': data['ID'], **self.scoring(data, arguments.llm_endpoint)}
                if contain_original_data:
                    result['original_data'] = data
                results.append(result)
            except Exception as e:
                print(repr(e))

        results = sorted(results, key=lambda x: x['id']) if sort else results
        valid_results = self.remove_invalid(results)

        try:
            overall = self.compute_overall(valid_results) if len(valid_results) > 0 else {}
        except Exception as e:
            print(repr(e))
            overall = dict()

        output = {'overall': overall, 'results': results}
        self.save_output(output)
        print(f"Output saved to {self.output_path}!")
        return output