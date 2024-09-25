from datasets import Dataset, load_dataset
import jsonlines
import os

class RAGDataset:

    """
        Dataset class to store data in HF datasets API format
    """

    def __init__(self, dataset, field_map, mode):
        self.dataset = dataset
        self.field_map = field_map
        assert mode in ["local", "benchmarking"], "mode can be either local or benchmarking"
        self.mode = mode
        self.data = self.load_data()
        self.validate_dataset()

    def load_data(self):
        if self.mode == "local":
            assert os.path.exists(self.dataset), "There is no such file - {}".format(self.dataset)
            with jsonlines.open(self.dataset) as reader:
                data = []
                for obj in reader:
                    ex = {}
                    for out_field, in_field in self.field_map.items():
                        if type(obj[in_field]) == list:
                            ex[out_field] = '\n'.join(obj[in_field])
                        else:
                            ex[out_field] = obj[in_field]
                    data.append(ex)
            return Dataset.from_list(data)
        else:
            data = []
            for obj in load_dataset(self.dataset)['train']:
                ex = {}
                for out_field, in_field in self.field_map.items():
                    if type(obj[in_field]) == list:
                        ex[out_field] = '\n'.join(obj[in_field])
                    else:
                        ex[out_field] = obj[in_field]
                data.append(ex)
            return Dataset.from_list(data)

    def validate_dataset(self):
        for i, example in enumerate(self.data):
            for out_field in self.field_map:
                assert out_field in example, "Example {} does not have {} field".format(i + 1, out_field)

    def __getitem__(self, index):
        return self.data[index]
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)
            
if __name__ == "__main__":

    dataset_path = '../../benchmark/ragas/ground_truth.jsonl'
    field_map = {
        'question' : 'question',
        'ground_truth' : 'ground_truth',
        'context' : 'context',
    }

    ds = RAGDataset(dataset=dataset_path,
                    field_map=field_map, 
                    mode="local")
    
    for i, ex in enumerate(ds):
        assert ex['question'] == ds[i]['question'], "index {} does not have correct query".format(i)

    dataset = "explodinggradients/ragas-wikiqa"
    field_map = {
        'question' : 'question',
        'answer' : 'generated_with_rag',
        'context' : 'context',
        'ground_truth' : 'correct_answer'
    }
    ds = RAGDataset(dataset=dataset, field_map=field_map, mode="benchmarking")

    for i, ex in enumerate(ds):
        assert ex['question'] == ds[i]['question'], "index {} does not have correct query".format(i)



