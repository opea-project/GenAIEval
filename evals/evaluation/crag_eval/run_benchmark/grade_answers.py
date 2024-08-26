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
    metric.measure(test_case)
    print(metric.score)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--llm_endpoint", type=str, default="http://localhost:8008")
    parser.add_argument("--filedir", type=str, help="Path to the file containing the data")
    parser.add_argument("--filename", type=str, help="Name of the file containing the data")
    args = parser.parse_args()

    data = pd.read_csv(os.path.join(args.filedir, args.filename))
    data = data.head(2)
    print(data)
    test_case = convert_data_format_for_ragas(data)
    print(test_case)
    grade_answers(args, test_case)

