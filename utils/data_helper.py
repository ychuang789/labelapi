import random

from collections import defaultdict
from typing import Dict, Iterator

import pandas as pd

from utils.input_example import InputExample


def load_examples(file: str, sample_count: int = None, shuffle: bool = True, labels=None):
    """
    讀取訓練資料
    Args:
        file: csv檔案路徑
        sample_count: 每個類別抽樣數量
        shuffle: 打亂順序
        labels: 使用標籤，若為None則使用全部
    Returns:

    """
    df = pd.read_csv(file, sep='\t', header=0, names=["content", "label"])

    examples = defaultdict(list)
    for index, row in df.iterrows():
        if labels is None or row['label'] in labels:
            examples[row['label']].append(
                InputExample(
                    id_=index,
                    s_area_id="",
                    author="",
                    title="",
                    content=row["content"],
                    post_time=None,
                    label=row["label"])
            )
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
