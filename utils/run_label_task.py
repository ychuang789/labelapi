from typing import Dict, Iterable

from models.audience_models import RuleModel, KeywordModel
from settings import ModelType, PredictTarget
from utils.input_example import InputExample


def run_prediction(input_examples: Iterable[InputExample], pattern: Dict,
                   model_type = ModelType.RULE_MODEL,
                   predict_type = PredictTarget.AUTHOR_NAME):
    if model_type == "rule_model":
        label_model = RuleModel(pattern)
        matched_labels, match_count_list = label_model.predict(input_examples, target=predict_type)
        return matched_labels, match_count_list
    elif model_type == "keyword_model":
        label_model = KeywordModel(pattern)
        matched_labels, match_count_list = label_model.predict(input_examples, target=predict_type)
        return matched_labels, match_count_list


def convert_input_data(df):
    [(Reading(row.HourOfDay, row.Percentage)) for index, row in df.iterrows()]
