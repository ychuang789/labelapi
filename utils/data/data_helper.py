import random

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterator, Union, List, Any, Tuple

import pandas as pd
from utils.data.input_example import InputExample
from workers.orm_core.table_creator import TermWeights


def load_examples(data: Union[str, List[Dict[str, Any]]],
                  sample_count: int = None, shuffle: bool = True,
                  labels=None):
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


def get_term_weights_from_file(task_id: str,
                               term_weight_list: List[dict]) -> List[TermWeights]:
    output_list = []
    for term_weight in term_weight_list:
        output_list.append(
            TermWeights(
                label=term_weight['label'],
                term=term_weight['term'],
                weight=term_weight['weight'],
                task_id=task_id
            )
        )

    return output_list


def get_term_weights_objects(task_id: str,
                             term_weight_dict: Dict[str, List[Tuple[str, float]]]) -> List[TermWeights]:
    term_weight_list = []
    for label, term_info in term_weight_dict.items():
        for term, weight in term_info:
            term_weight_list.append(TermWeights(label=label, term=term, weight=weight, task_id=task_id))

    return term_weight_list


def read_csv_to_dict(file_path: Path) -> Dict:
    df = pd.read_csv(file_path, encoding='utf-8')

    _dict = {}
    for _, row in df.iterrows():
        temp_dict = {
            row.source_id: row.table
        }
        _dict.update(temp_dict)

    return _dict


def orm_queryset_to_dict(record):
    result_dict = {}
    for c in record.__table__.columns:
        if isinstance(getattr(record, c.name), datetime):
            result_dict[c.name] = getattr(record, c.name).strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(getattr(record, c.name), Decimal):
            result_dict[c.name] = float(getattr(record, c.name))
        else:
            result_dict[c.name] = getattr(record, c.name)
    return result_dict


def list_dict_to_csv(dataset: List[dict], filename: str):
    if not filename.endswith('.csv'):
        filename += '.csv'
    df = pd.DataFrame(dataset)
    df.to_csv(filename, encoding='utf-8', index=False)


def queryset_to_csv(records: list, filename: str):
    list_dict_to_csv([orm_queryset_to_dict(record) for record in records], filename)
