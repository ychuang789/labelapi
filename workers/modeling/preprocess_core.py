import codecs
import csv
import random

from collections import defaultdict
from typing import Dict, List, Any, Union, Iterator

import cchardet
import pandas as pd

from settings import LOCAL_TEST
from utils.data.input_example import InputExample
from utils.database.connection_helper import DBConnection, ConnectionConfigGenerator, QueryManager
from utils.exception_manager import DataNotFoundError
from utils.enum_config import DatasetType, RuleType
from workers.orm_core.table_creator import Rules


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

    def get_rules(self, task_id: str) -> List[Rules]:
        rules = self.get_source_rules(local_test=LOCAL_TEST)
        if not rules:
            raise ValueError('rules are not found')
        rule_bulk_list = []
        for rule in rules:
            rule_bulk_list.append(
                Rules(content=rule['content'],
                      rule_type=rule['rule_type'],
                      score=rule['score'],
                      label=rule['name'],
                      match_type=rule['match_type'],
                      task_id=task_id)
            )
        return rule_bulk_list

    def load_rules(self, rules: List[Rules]):
        rules_dict = defaultdict(list)
        for rule in rules:
            if rule.rule_type == RuleType.REGEX.value:
                rules_dict[rule.label].append(str(rule.content))
            elif rule.rule_type == RuleType.KEYWORD.value:
                rules_dict[rule.label].append((rule.content, rule.match_type))
            else:
                raise ValueError(f"{rule.rule_type} is not a proper rule type for the task")
        return dict(rules_dict)

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

    def preprocess_example(self, examples: dict, sample_count: int = None, shuffle: bool = True) -> Iterator[InputExample]:
        dataset = []
        for label, rows in examples.items():
            if sample_count and len(rows) >= sample_count:
                dataset.extend(random.sample(rows, sample_count))
            else:
                dataset.extend(rows)
        if shuffle:
            random.shuffle(dataset)
        return dataset

    def get_source_dataset(self, **condition):
        return DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                          **ConnectionConfigGenerator.rd2_database(schema=self.dataset_schema))

    def get_source_rules(self, local_test: bool = False):
        if local_test:
            return DBConnection.execute_query(query=QueryManager.get_rule_query(labeling_job_id=self.dataset_number),
                                              **ConnectionConfigGenerator.test_database(schema=self.dataset_schema))
        else:
            return DBConnection.execute_query(query=QueryManager.get_rule_query(labeling_job_id=self.dataset_number),
                                              **ConnectionConfigGenerator.rd2_database(schema=self.dataset_schema))

    @staticmethod
    def read_csv_file(file, required_fields):
        delimiters = [',', '\t']
        encoding = cchardet.detect(file.read())['encoding']
        file.seek(0)
        csv_file = header = exist_field = None
        for delimiter in delimiters:
            csv_file = csv.DictReader(codecs.iterdecode(file, encoding), skipinitialspace=True,
                                      delimiter=delimiter,
                                      quoting=csv.QUOTE_ALL)
            header = csv_file.fieldnames
            print(header)
            if isinstance(required_fields, dict):
                if len(set(required_fields.keys()).intersection(header)) > 0:
                    exist_field = set(required_fields.keys()).intersection(header)
                    break
                elif len(set(required_fields.values()).intersection(header)) > 0:
                    exist_field = set(required_fields.values()).intersection(header)
                    break
            else:
                if len(set(required_fields).intersection(header)) > 0:
                    exist_field = set(required_fields).intersection(header)
                    break
        if csv_file is None or exist_field is None:
            raise ValueError(f"csv欄位讀取錯誤，請確認所使用的欄位分隔符號是否屬於於「{' or '.join(delimiters)}」其中一種。")

        return csv_file
