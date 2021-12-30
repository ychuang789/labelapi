import re
from typing import Iterable, Dict, List

from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer

from models.audience_model_interfaces import RuleBaseModel
from utils.input_example import InputExample

from utils.selections import ModelType, PredictTarget, Errors



class RuleModel(RuleBaseModel):
    def __init__(self, model_dir_name= None,
                 patterns: Dict[str, List[str]] = None,
                 name: str = None,
                 model_type: ModelType = ModelType.RULE_MODEL,
                 feature: PredictTarget = PredictTarget.CONTENT,
                 verbose: bool = False):
        super().__init__(name=name if name is not None else "RuleModel",
                         model_dir_name=model_dir_name,
                         model_type=model_type, feature=feature,
                         logger_name="RuleModel", verbose=verbose)
        self.logger.debug("model Init")
        self.label_patterns = None
        self.labels = []
        if patterns:
            self.load(patterns)

    def load(self, label_patterns: Dict[str, List[str]] = None):
        self.label_patterns = label_patterns
        self.labels = [label for label in self.label_patterns.keys()]
        self.logger.debug(f"labels size: {len(self.labels)}")
        self.mlb = MultiLabelBinarizer(classes=list(label_patterns.keys()))
        self.mlb.fit([[label] for label in list(label_patterns.keys())])
        # print(self.mlb.classes)

    def predict(self, input_examples: Iterable[InputExample],
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

                for pattern in patterns:
                    if re.search(pattern=pattern, string=_predict_str.lower()):
                        _matched_count += 1


                if _matched_count > 0:
                    _match_count_list.append((label, _matched_count))
                    _matched_labels.append(label)

            if len(_matched_labels) > 0:
                matched_labels.append(tuple(_matched_labels))
                match_count_list.append(_match_count_list)

        self.logger.debug(f"Matched labels size: {len(matched_labels)}")
        self.logger.debug(f"Matched count list size: {len(match_count_list)}")
        if len(matched_labels) > 0:
            return matched_labels, match_count_list
        else:
            return None, None

    def eval(self, examples: List[InputExample], y_true):
        for index, y in enumerate(y_true):
            y_true[index] = y

        if self.label_patterns and self.mlb:
            predict_labels, first_matched_keyword = self.predict(examples)
            y_true = self.mlb.transform(y_true)
            y_pred = self.mlb.transform(predict_labels)
            acc = accuracy_score(y_true=y_true, y_pred=y_pred)
            report = classification_report(y_true=y_true, y_pred=y_pred, output_dict=True, zero_division=1,
                                           target_names=self.mlb.classes)
            report['accuracy'] = acc
            return report
        else:
            raise ValueError(f"模型尚未被訓練，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")

def parse_predict_target(input_examples: Iterable[InputExample], target: PredictTarget = PredictTarget.CONTENT.value,
                         case_sensitive: bool = False) -> List[str]:
    return [_parse_predict_target(input_example, target=target, case_sensitive=case_sensitive)
            for input_example in input_examples]

def _parse_predict_target(input_example: InputExample, target: PredictTarget = PredictTarget.CONTENT.value,
                          case_sensitive: bool = False) -> str:
    if target == PredictTarget.CONTENT.value:
        return input_example.content if case_sensitive else input_example.content.lower()
    elif target == PredictTarget.AUTHOR_NAME.value:
        return input_example.author if case_sensitive else input_example.author.lower()
    elif target == PredictTarget.S_AREA_ID.value:
        return input_example.s_area_id if case_sensitive else input_example.s_area_id.lower()
    else:
        raise ValueError(Errors.UNKNOWN_PREDICT_TARGET_TYPE)
