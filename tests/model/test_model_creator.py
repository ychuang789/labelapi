from unittest import TestCase

from models.rule_based_models.keyword_model import KeywordModel
from models.model_creator import ModelSelector
from models.trainable_models.rf_model import RandomForestModel
from models.rule_based_models.rule_model import RuleModel
from models.trainable_models.tw_model import TermWeightModel
from utils.selections import KeywordMatchType, ModelType, PredictTarget


class TestModelCreator(TestCase):

    keyword_patterns = {"female": [("woman_talk", KeywordMatchType.END), ("_talk", KeywordMatchType.PARTIALLY)]}
    regex_patterns = {"young": ["工作.{0,3}([一兩三]|[1-3])年"]}
    model_path = "0_model"

    def test_create_rule_model(self):
        model_information = {"patterns": self.regex_patterns}
        self.assertIsInstance(ModelSelector.rule_based_model(ModelType.RULE_MODEL.name,
                                                             PredictTarget.CONTENT.name,
                                                             **model_information),
                              RuleModel)

    def test_create_keyword_model(self):
        model_information = {"patterns": self.keyword_patterns}
        self.assertIsInstance(ModelSelector.rule_based_model(ModelType.KEYWORD_MODEL.name,
                                                             PredictTarget.AUTHOR_NAME.name,
                                                             **model_information),
                              KeywordModel)

    def test_create_random_forest_model(self):
        model_information = {"model_path": self.model_path}
        self.assertIsInstance(ModelSelector.trainable_model(ModelType.RANDOM_FOREST_MODEL.name,
                                                             PredictTarget.CONTENT.name,
                                                            **model_information),
                              RandomForestModel)

    def test_create_term_weight_model(self):
        model_information = {"model_path": self.model_path}
        self.assertIsInstance(ModelSelector.trainable_model(ModelType.TERM_WEIGHT_MODEL.name,
                                                             PredictTarget.CONTENT.name,
                                                            **model_information),
                              TermWeightModel)

    def test_create_model_obj1(self):
        model_name = "RANDOM_FOREST_MODEL"
        model_info = {"model_path": self.model_path}
        model = ModelSelector(model_name=model_name, target_name=PredictTarget.CONTENT, **model_info)
        self.assertIsInstance(model.create_model_obj(), RandomForestModel)

    def test_create_model_obj2(self):
        model_name = "KEYWORD_MODEL"
        model_info = {"model_path": self.model_path, "patterns": self.keyword_patterns}
        model = ModelSelector(model_name=model_name, target_name=PredictTarget.AUTHOR_NAME, **model_info)
        self.assertIsInstance(model.create_model_obj(), KeywordModel)








