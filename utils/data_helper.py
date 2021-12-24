import random

from collections import defaultdict
from typing import Dict, Iterator, Union, List, Any

import pandas as pd

from utils.connection_helper import DBConnection, ConnectionConfigGenerator, QueryManager
from utils.input_example import InputExample

class PreprocessWorker:
    def run_processing(self, dataset_number, dataset_schema, sample_count=1000):
        data_dict = {}
        for i in ['train', 'dev', 'test']:
            condition = {'labeling_job_id': dataset_number, 'document_type': i}
            data = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                              **ConnectionConfigGenerator.rd2_database(schema=dataset_schema))
            data = load_examples(data=data, sample_count=sample_count)
            data_dict.update({i: data})
        return data_dict


def load_examples(data: Union[str, List[Dict[str, Any]]],
                  sample_count: int = None, shuffle: bool = True,
                  labels=None):
    examples = defaultdict(list)
    if isinstance(data, list):
        df = pd.DataFrame(data)

        for index, row in df.iterrows():
            if not labels or row['label'] in labels:
                examples[row['label']].append(
                    InputExample(
                        id_=row['id'],
                        s_area_id=row['s_area_id'],
                        author=row['author'],
                        title=row['title'],
                        content=row["content"],
                        post_time=row['post_time'],
                        label=row["name"])
                )
    elif isinstance(data, str):
        df = pd.read_csv(data, sep='\t', header=0, names=["content", "label"])
        for index, row in df.iterrows():
            if not labels or row['label'] in labels:
                examples[row['label']].append(
                    InputExample(
                        id_=index,
                        s_area_id="",
                        author="",
                        title="",
                        content=row["content"],
                        post_time=None,
                        label=row["name"])
                )
    else:
        raise TypeError(f"Expect input data type as str or list, "
                        f"got {type(data)} instead")

    return preprocess_example(examples=examples, sample_count=sample_count, shuffle=shuffle)

def preprocess_example(examples: Dict, sample_count: int = None, shuffle: bool = True) -> Iterator[InputExample]:
    dataset = []
    for label, rows in examples.items():
        if sample_count and len(rows) >= sample_count:
            dataset.extend(random.sample(rows, sample_count))
        else:
            dataset.extend(rows)
    if shuffle:
        random.shuffle(dataset)
    return dataset
