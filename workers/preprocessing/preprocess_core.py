import csv
import random

from collections import defaultdict
from itertools import groupby
from typing import Dict, List, Any, Union, Iterator, Tuple

import pandas as pd

from utils.data.input_example import InputExample
from utils.exception_manager import DataNotFoundError
from utils.enum_config import DatasetType, RuleType
from workers.orm_core.document_operation import DocumentCRUD
from workers.orm_core.table_creator import Rules
from workers import data_filter_builder


class PreprocessWorker:

    def __init__(self, dataset_number, dataset_schema, model_type = None):
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema
        self.model_type = model_type

    def __str__(self):
        return f"the class for data preprocessing"

    def run_processing(self, sample_count=1000, is_train=True):
        # todo: refactor

        dataset = self.get_source_dataset()
        sorted_dataset = sorted(dataset, key=key_func)
        if is_train:
            data_dict = {}
            for k,v in groupby(sorted_dataset, key_func):
                if k == DatasetType.EXT_TEST.value:
                    continue
                if not list(v):
                    raise DataNotFoundError('There are missing data from database')

                data = self.load_examples(data=list(v), sample_count=sample_count)
                data_dict.update({k: data})
            return data_dict

            # for i in [t.value for t in DatasetType]:
            #     if i == DatasetType.EXT_TEST.value:
            #         continue
            #     condition = {'labeling_job_id': self.dataset_number, 'document_type': i}
            #     data = self.get_source_dataset(**condition)
            #
            #     if not data:
            #         raise DataNotFoundError('There are missing data from database')
            #     data = self.load_examples(data=data, sample_count=sample_count)
            #     data_dict.update({i: data})

        else:
            for k,v in groupby(sorted_dataset, key_func):
                if k == DatasetType.EXT_TEST.value:
                    if not list(v):
                        raise DataNotFoundError('There are missing data from database')
                    if not list(v):
                        raise DataNotFoundError('There are missing data from database')
                    data = self.load_examples(data=list(v), sample_count=sample_count)
                    return data

            # condition = {'labeling_job_id': self.dataset_number, 'document_type': DatasetType.EXT_TEST.value}
            # data = self.get_source_dataset(**condition)

    def get_rules(self, task_id: str) -> List[Rules]:
        # todo: refactor get_source_rules
        # rules = self.get_source_rules(local_test=LOCAL_TEST)
        rules = self.get_source_rules()
        if not rules:
            raise ValueError('rules are not found')
        rule_bulk_list = []
        for rule in rules:
            rule_bulk_list.append(
                Rules(content=rule['content'],
                      rule_type=rule['rule_type'],
                      score=rule.get('score', 1),
                      label=rule['label'],
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

        # return self.preprocess_example(examples=examples, sample_count=sample_count, shuffle=shuffle)
        return self.preprocess_example(examples=data_filter_builder.model_dataset_cleaning(examples),
                                       sample_count=sample_count, shuffle=shuffle)

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

    def get_source_dataset(self):
        doc_worker = DocumentCRUD()
        dataset = doc_worker.dataset_render(self.dataset_number)
        return [doc_worker.orm_cls_to_dict(data) for data in dataset]
        # return DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
        #                                   **ConnectionConfigGenerator.rd2_database(schema=self.dataset_schema))

    def get_source_rules(self):
        doc_worker = DocumentCRUD()
        rules = doc_worker.rule_render(self.dataset_number)
        doc_worker.dispose()
        return [doc_worker.orm_cls_to_dict(r) for r in rules]
        # < v2.4
        # if local_test:
        #     return DBConnection.execute_query(query=QueryManager.get_rule_query(labeling_job_id=self.dataset_number),
        #                                       **ConnectionConfigGenerator.test_database(schema=self.dataset_schema))
        # else:
        #     return DBConnection.execute_query(query=QueryManager.get_rule_query(labeling_job_id=self.dataset_number),
        #                                       **ConnectionConfigGenerator.rd2_database(schema=self.dataset_schema))

    @staticmethod
    def read_csv_file(filepath):
        with open(filepath, 'r') as f:
            rows = csv.DictReader(f)
            output_list = [row for row in rows]
            return output_list

    @staticmethod
    def load_term_weight_from_db(term_weight_set: List[dict]) -> Dict[str, List[Tuple[str, float]]]:
        output_dict = defaultdict(list)
        for term_weight in term_weight_set:
            output_dict[term_weight['label']].append((term_weight['term'], term_weight['weight']))

        return output_dict


def key_func(dicts, group_key='dataset_type'):
    return dicts[group_key]
