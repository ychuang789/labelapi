from abc import ABC, abstractmethod
from models.keyword_model import KeywordModel
from models.rf_model import RandomForestModel
from models.rule_model import RuleModel
from models.tw_model import TermWeightModel
from utils.selections import ModelType, PredictTarget

class TWFeatureModelNotFoundError(Exception):
    pass

class ModelTypeNotFoundError(Exception):
    pass

class ParamterMissingError(Exception):
    pass

class ModelHandler(ABC):
    """The model handler interface which model creator should implement"""
    @staticmethod
    @abstractmethod
    def create_model(type_attribute: str, target_attribute: str, **kwargs):
        """create a model"""

class TrainableModelCreator(ModelHandler):
    @staticmethod
    def create_model(type_attribute: str, target_attribute: str, **kwargs):
        if not hasattr(ModelType, type_attribute) or not hasattr(PredictTarget, target_attribute):
            raise ModelTypeNotFoundError(f'{type_attribute} or {target_attribute} is not in default type configuration')
        else:
            type_attribute = type_attribute.lower()

        if type_attribute == ModelType.RANDOM_FOREST_MODEL.value:
            if not (model_path := kwargs.get('model_path')):
                raise ParamterMissingError(f'model_path')
            return RandomForestModel(model_dir_name=model_path, feature=PredictTarget[target_attribute])
        elif type_attribute == ModelType.TERM_WEIGHT_MODEL.value:
            if not (model_path := kwargs.get('model_path')):
                raise ParamterMissingError(f'model_path')
            return TermWeightModel(model_dir_name=model_path, feature=PredictTarget[target_attribute])
        else:
            raise ModelTypeNotFoundError(f'{type_attribute} is unknown')


class RuleBasedModelCreator(ModelHandler):
    @staticmethod
    def create_model(type_attribute: str, target_attribute: str = None, **kwargs):
        if not hasattr(ModelType, type_attribute) or not hasattr(PredictTarget, target_attribute):
            raise ModelTypeNotFoundError(f'{type_attribute} or {target_attribute} is not in default type configuration')
        else:
            type_attribute = type_attribute.lower()

        if type_attribute == ModelType.KEYWORD_MODEL.value:
            if not (keyword_patterns := kwargs.get('keyword_patterns')):
                raise ParamterMissingError(f'keyword patterns')
            return KeywordModel(label_keywords=keyword_patterns, target=PredictTarget[target_attribute])

        elif type_attribute == ModelType.RULE_MODEL.value:
            if not (regex_patterns := kwargs.get('regex_patterns')):
                raise ParamterMissingError(f'regex patterns')
            return RuleModel(model_rules=regex_patterns, target=PredictTarget[target_attribute])
        else:
            raise ModelTypeNotFoundError(f'{type_attribute} is unknown')


class ModelSelector():

    @staticmethod
    def trainable_model(type_attribute: str, target_attribute: str, **kwargs):
        return TrainableModelCreator().create_model(type_attribute, target_attribute, **kwargs)

    @staticmethod
    def rule_based_model(type_attribute: str, target_attribute: str, **kwargs):
        return RuleBasedModelCreator().create_model(type_attribute, target_attribute, **kwargs)


