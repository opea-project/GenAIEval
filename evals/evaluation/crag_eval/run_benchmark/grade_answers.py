from evals.metrics.ragas import RagasMetric
from ragas.metrics import answer_correctness
import argparse
import pandas as pd
import os

def convert_data_format_for_ragas(data):
    # data: pandas dataframe
    # columns: ['query', 'answer', 'ref_answer']
    # return: a dict with keys: 'input', 'actual_output', 'expected_output'
    output = {
        'input': data['query'].tolist(),
        'actual_output': data['answer'].tolist(),
        'expected_output': data['ref_answer'].tolist(),
        'retrieval_context': [["dummy_context"] for _ in range(data['query'].shape[0])]
    }
    return output


def make_list_of_test_cases(data):
    # data: pandas dataframe
    # columns: ['query', 'answer', 'ref_answer']
    # return: a list of dicts with keys: 'input', 'actual_output', 'expected_output'
    output = []
    for _, row in data.iterrows():
        output.append(
            {
                'input': [row['query']],
                'actual_output': [row['answer']],
                'expected_output': [row['ref_answer']],
                'retrieval_context': [["dummy_context"]]
            }
        )
    return output

def grade_answers(args, test_case):
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings
    print('==============getting embeddings==============')
    embeddings = HuggingFaceBgeEmbeddings(model_name=args.embed_model)
    print('==============initiating metric==============')
    metric = RagasMetric(threshold=0.5, 
                         metrics=["answer_correctness"],
                         model= args.llm_endpoint, 
                         embeddings=embeddings)
    print('==============start grading==============')

    if args.batch_grade:
        metric.measure(test_case)
        return metric.score
    else:
        scores = []
        for case in test_case:
            metric.measure(case)
            scores.append(metric.score)
            print(metric.score)
            print('-'*50)
        return scores

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--llm_endpoint", type=str, default="http://localhost:8008")
    parser.add_argument("--filedir", type=str, help="Path to the file containing the data")
    parser.add_argument("--filename", type=str, help="Name of the file containing the data")
    parser.add_argument("--batch_grade", action="store_true", help="Grade the answers in batch and get an aggregated score for the entire dataset")
    args = parser.parse_args()

    data = pd.read_csv(os.path.join(args.filedir, args.filename))
    data = data.head(2)
    print(data)
    if args.batch_grade:
        test_case = convert_data_format_for_ragas(data)
    else:
        test_case = make_list_of_test_cases(data)
    
    print(test_case)
    scores = grade_answers(args, test_case)
    print(scores)

