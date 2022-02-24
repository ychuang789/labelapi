from typing import List

from models.rule_based_models.keyword_model import KeywordModel
from models.rule_based_models.regex_model import RegexModel
from utils.data.input_example import InputExample


class DataFilterWorker:
    def __init__(self, dataset: List[InputExample], target):
        self.dataset = dataset
        self.keyword_model = KeywordModel(feature=target)
        self.regex_model = RegexModel(feature=target)

    def run_task(self):
        pass

    def check_data_to_delete(self, row_data):
        pass

