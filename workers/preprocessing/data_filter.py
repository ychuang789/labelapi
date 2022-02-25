import importlib
import itertools
import re
from collections import defaultdict
from typing import List

from settings import DatabaseConfig, MODEL_INFORMATION
from utils.data.input_example import InputExample
from utils.enum_config import ModelType, FilterRuleLabel
from utils.exception_manager import ModelTypeNotFoundError
from workers.orm_core.preprocess_operation import PreprocessCRUD


class DataFilterWorker:
    def __init__(self, filter_task_id: int, dataset: List[InputExample]):
        self.dataset = dataset
        self.orm = PreprocessCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
        self.task = self.orm.get_task(task_pk=filter_task_id)
        self.model = self.get_model()

    def run_task(self):
        output_list = []

        if self.task.name in FilterRuleLabel.DELETE:
            for data in self.dataset:
                if self.check_data_delete:
                    continue
                output_list.append(data)
        elif self.task.name in FilterRuleLabel.ALTER:
            for data in self.dataset:
                output_list.append(self.check_data_alter(data))
        else:
            raise ValueError(f'{self.task.name} is a unknown task')

        return output_list

    def check_data_alter(self, row_data: InputExample):
        label, prob = self.model.predict([row_data])

        if not label:
            return row_data

        for i in prob[0]:
            if self.task.model_name == ModelType.REGEX_MODEL.name:
                row_data = alter(row_data, sub_list=i[1])
            if self.task.model_name == ModelType.KEYWORD_MODEL.name:
                row_data = alter(row_data, sub_list=[j[0] for j in itertools.chain(*i[1])])

        return row_data

    def alter(self, row_data, sub_list):
        for s in sub_list:
            temp_data = re.sub(s, "", getattr(row_data, self.task.feature))
            setattr(row_data, self.task.feature, temp_data)
        return row_data

    def check_data_delete(self, row_data: InputExample):
        label, prob = self.model.predict([row_data])

        if label:
            return True
        else:
            return False

    def get_model(self):
        temp_rule_set = self.task.filter_rules_collection
        model_class, _ = get_model_class(task=self.task)
        model = model_class(feature=self.task.feature,
                            patterns=load_pattern(rule_set=temp_rule_set,
                                                  model_type=self.task.model_name))
        return model


def get_model_class(task):
    if task.model_name in MODEL_INFORMATION:
        module_path, class_name = MODEL_INFORMATION.get(task.model_name).rsplit(sep='.', maxsplit=1)
        return getattr(importlib.import_module(module_path), class_name), class_name
    else:
        raise ModelTypeNotFoundError(f'{task.model_name} is not a available model')


def load_pattern(rule_set, model_type):
    if not rule_set:
        raise ValueError(f'Pattern are missing')
    rules_dict = defaultdict(list)
    for rule in rule_set:
        if model_type == ModelType.REGEX_MODEL.name:
            rules_dict[rule.label].append(str(rule.content))
        elif model_type == ModelType.KEYWORD_MODEL.name:
            rules_dict[rule.label].append((rule.content, rule.match_type))
        else:
            raise ValueError(f"{rule.rule_type} is not a proper rule type for the task")
    return rules_dict



