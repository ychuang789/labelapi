import re
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple, Iterable, Any

from utils.helper import get_logger
from utils.input_example import InputExample
from utils.settings import Errors, ModelType, PredictTarget

class AudienceModel(ABC):
    def __init__(self, name: str, model_type: ModelType, case_sensitive: bool = False,
                 target: PredictTarget = PredictTarget.CONTENT,
                 logger_name: str = "AudienceModel",
                 verbose: bool = False):
        self.name = name
        self.model_type = model_type
        self.case_sensitive = case_sensitive
        self.target = target
        self.meta = {}
        self.labels = None
        self.logger = get_logger(logger_name, verbose=verbose)

    @abstractmethod
    def load(self, label_patterns):
        pass

    @abstractmethod
    def predict(self, input_examples: Iterable[InputExample], bypass_labels: Set = None):
        pass



class RuleModel(AudienceModel):
    def __init__(self, model_data: Dict[str, List[str]] = None,
                 name: str = None,
                 model_type: ModelType = ModelType.RULE_MODEL,
                 target: PredictTarget = PredictTarget.CONTENT,
                 na_label=None,
                 verbose: bool = False):
        super().__init__(name=name if name is not None else "RuleModel", model_type=model_type, target=target,
                         logger_name="RuleModel", verbose=verbose)
        self.logger.debug("model Init")
        self.label_patterns = None
        self.na_label = na_label
        self.labels = []
        if model_data is not None:
            self.load(model_data)

    def load(self, label_patterns: Dict[str, List[str]] = None):
        self.label_patterns = label_patterns
        self.labels = [label for label in self.label_patterns.keys()]
        self.logger.debug(f"labels size: {len(self.labels)}")

    def predict(self, input_examples: Iterable[InputExample], bypass_labels: Set = None,
                target=None):
        target = target if target is not None else self.target
        x = parse_predict_target(input_examples=input_examples, target=target,
                                 case_sensitive=self.case_sensitive)
        matched_labels = []
        match_count_list = []
        for _predict_str in x:
            _match_count_list = []
            _matched_labels = []
            for label, patterns in self.label_patterns.items():
                _matched_count = 0
                if bypass_labels and label in bypass_labels:
                    continue
                for pattern in patterns:
                    if re.search(pattern=pattern, string=_predict_str.lower()):
                        _matched_count += 1
                        # matched_result[label] = True
                        # break
                    # else:
                    # matched_result[cat] = False

                if _matched_count > 0:
                    _match_count_list.append((label, _matched_count))
                    _matched_labels.append(label)

            if len(_matched_labels) > 0:
                matched_labels.append(tuple(_matched_labels))
                match_count_list.append(_match_count_list)
            else:
                matched_labels.append(tuple([self.na_label]))
                match_count_list.append([(self.na_label, 1)])
        self.logger.debug(f"Matched labels size: {len(matched_labels)}")
        self.logger.debug(f"Matched count list size: {len(match_count_list)}")
        if len(matched_labels) > 0:
            return matched_labels, match_count_list
        else:
            return None, None


def parse_predict_target(input_examples: Iterable[InputExample], target: PredictTarget = PredictTarget.CONTENT,
                         case_sensitive: bool = False) -> List[str]:
    return [_parse_predict_target(input_example, target=target, case_sensitive=case_sensitive)
            for input_example in input_examples]


def _parse_predict_target(input_example: InputExample, target: PredictTarget = PredictTarget.CONTENT,
                          case_sensitive: bool = False) -> str:
    if target == PredictTarget.CONTENT:
        return input_example.content if case_sensitive else input_example.content.lower()
    elif target == PredictTarget.AUTHOR_NAME:
        return input_example.author if case_sensitive else input_example.author.lower()
    elif target == PredictTarget.S_AREA_ID:
        return input_example.s_area_id if case_sensitive else input_example.s_area_id.lower()
    else:
        raise ValueError(Errors.UNKNOWN_PREDICT_TARGET_TYPE)
