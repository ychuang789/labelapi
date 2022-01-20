from unittest import TestCase

from models.rule_based_models.keyword_model import KeywordModel
from models.model_creator import ModelSelector
from models.trainable_models.rf_model import RandomForestModel
from utils.enum_config import KeywordMatchType, PredictTarget


class TestModelCreator(TestCase):

    keyword_patterns = {"female": [("woman_talk", KeywordMatchType.END), ("_talk", KeywordMatchType.PARTIALLY)]}
    regex_patterns = {"young": ["工作.{0,3}([一兩三]|[1-3])年"]}
    model_path = "0_model"


    def test_create_model_obj1(self):
        model_name = "RANDOM_FOREST_MODEL"
        model_info = {"model_path": self.model_path}
        model = ModelSelector(model_name=model_name, target_name=PredictTarget.CONTENT, **model_info)
        self.assertIsInstance(model.create_model_obj(), RandomForestModel)

    def test_create_model_obj2(self):
        model_name = "KEYWORD_MODEL"
        model_info = {"model_path": self.model_path, "patterns": self.keyword_patterns}
        model = ModelSelector(model_name=model_name, target_name=PredictTarget.AUTHOR, **model_info)
        self.assertIsInstance(model.create_model_obj(), KeywordModel)


    def test_create_model_obj_exception1(self):
        """models.model_creator.ModelTypeNotFoundError: KEYWORD_ is not a available model"""
        model_name = "KEYWORD_"
        model_info = {"model_path": self.model_path, "patterns": self.keyword_patterns}
        model = ModelSelector(model_name=model_name, target_name=PredictTarget.AUTHOR, **model_info)
        self.assertIsInstance(model.create_model_obj(), KeywordModel)

    def test_create_model_obj_exception2(self):
        """models.model_creator.ParamterMissingError: patterns are missing"""
        model_name = "KEYWORD_MODEL"
        model_info = {"model_path": self.model_path}
        model = ModelSelector(model_name=model_name, target_name=PredictTarget.AUTHOR, **model_info)
        self.assertIsInstance(model.create_model_obj(), KeywordModel)







