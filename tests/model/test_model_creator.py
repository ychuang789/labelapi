from unittest import TestCase

from models.keyword_model import KeywordModel
from models.model_creator import TrainableModelCreator
from models.rf_model import RandomForestModel
from models.rule_model import RuleModel
from models.tw_model import TermWeightModel
from utils.selections import KeywordMatchType, ModelType


class TestModelCreator(TestCase):

    keyword_patterns = {"female": [("woman_talk", KeywordMatchType.END), ("_talk", KeywordMatchType.PARTIALLY)]}
    regex_patterns = {"young": ["工作.{0,3}([一兩三]|[1-3])年"]}
    model_path = "0_supervised_models"

    model_information = {"keyword_patterns": keyword_patterns,
                         "regex_patterns": regex_patterns,
                         "model_path": model_path}

    def test_create_rule_model(self):
        self.assertIsInstance(TrainableModelCreator.create_model(ModelType.RULE_MODEL.name, **self.model_information),
                              RuleModel)

    def test_create_keyword_model(self):
        self.assertIsInstance(TrainableModelCreator.create_model(ModelType.KEYWORD_MODEL.name, **self.model_information),
                              KeywordModel)

    def test_create_random_forest_model(self):
        self.assertIsInstance(TrainableModelCreator.create_model(ModelType.RANDOM_FOREST_MODEL.name, 'CONTENT', **self.model_information),
                              RandomForestModel)

    def test_create_term_weight_model(self):
        self.assertIsInstance(TrainableModelCreator.create_model(ModelType.TERM_WEIGHT_MODEL.name, 'AUTHOR_NAME', **self.model_information),
                              TermWeightModel)



