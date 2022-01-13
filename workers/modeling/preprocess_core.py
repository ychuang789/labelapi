import random

from collections import defaultdict
from typing import Dict, List, Any, Union, Iterator

import pandas as pd

from utils.data.input_example import InputExample
from utils.database.connection_helper import DBConnection, ConnectionConfigGenerator, QueryManager
from utils.exception_tool.exception_manager import DataNotFoundError
from utils.enum_config import DatasetType

class PreprocessWorker():

    def __init__(self, dataset_number, dataset_schema):
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema

    def __str__(self):
        return f"the class for data preprocessing"

    def run_processing(self, sample_count=1000, is_train=True):
        if is_train:
            data_dict = {}
            for i in [t.value for t in DatasetType]:
                if i == DatasetType.EXT_TEST.value:
                    continue
                condition = {'labeling_job_id': self.dataset_number, 'document_type': i}
                data = self.get_source_dataset(**condition)
                if not data:
                    raise DataNotFoundError('There are missing data from database')
                data = self.load_examples(data=data, sample_count=sample_count)
                data_dict.update({i: data})
            return data_dict
        else:
            condition = {'labeling_job_id': self.dataset_number, 'document_type': DatasetType.EXT_TEST.value}
            data = self.get_source_dataset(**condition)
            if not data:
                raise DataNotFoundError('There are missing data from database')
            data = self.load_examples(data=data, sample_count=sample_count)
        return data

    def get_source_dataset(self, **condition):
        return DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                          **ConnectionConfigGenerator.rd2_database(schema=self.dataset_schema))

    def load_examples(self, data: Union[str, List[Dict[str, Any]]],
                      sample_count: int = None, shuffle: bool = True, labels=None):
        examples = defaultdict(list)
        if isinstance(data, list):
            df = pd.DataFrame(data)
            for index, row in df.iterrows():
                if not labels or row['name'] in labels:
                    examples[row['name']].append(
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

        return self.preprocess_example(examples=examples, sample_count=sample_count, shuffle=shuffle)

    def preprocess_example(self, examples: Dict, sample_count: int = None, shuffle: bool = True) -> Iterator[InputExample]:
        dataset = []
        for label, rows in examples.items():
            if sample_count and len(rows) >= sample_count:
                dataset.extend(random.sample(rows, sample_count))
            else:
                dataset.extend(rows)
        if shuffle:
            random.shuffle(dataset)
        return dataset
