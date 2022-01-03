import importlib
from abc import ABC, abstractmethod
from typing import Union

from models.audience_model_interfaces import RuleBaseModel, SupervisedModel
from models.rule_based_models.keyword_model import KeywordModel
from models.trainable_models.rf_model import RandomForestModel
from models.rule_based_models.rule_model import RuleModel
from models.trainable_models.tw_model import TermWeightModel
from settings import MODEL_INFORMATION
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
            return RandomForestModel(model_dir_name=model_path, feature=PredictTarget[target_attribute], **kwargs)
        elif type_attribute == ModelType.TERM_WEIGHT_MODEL.value:
            if not (model_path := kwargs.get('model_path')):
                raise ParamterMissingError(f'model_path')
            return TermWeightModel(model_dir_name=model_path, feature=PredictTarget[target_attribute], **kwargs)
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
            if not (keyword_patterns := kwargs.get('patterns')):
                raise ParamterMissingError(f'keyword patterns')
            return KeywordModel(patterns=keyword_patterns, feature=PredictTarget[target_attribute])

        elif type_attribute == ModelType.RULE_MODEL.value:
            if not (regex_patterns := kwargs.get('patterns')):
                raise ParamterMissingError(f'regex patterns')
            return RuleModel(patterns=regex_patterns, feature=PredictTarget[target_attribute])
        else:
            raise ModelTypeNotFoundError(f'{type_attribute} is unknown')


class ModelSelector():
    """Select a model and create it"""

    def __init__(self, model_name: Union[str, ModelType], target_name: Union[str, PredictTarget],
                 is_train = True, **kwargs):
        self.model_name = model_name if isinstance(model_name, str) else model_name.value
        self.target_name = target_name if isinstance(target_name, str) else target_name.value
        self.model_path = kwargs.pop('model_path', None)
        self.pattern = kwargs.pop('patterns', None)
        self.is_train = is_train
        self.model_info = kwargs

    def get_model_class(self, model_name: str):
        if model_name in MODEL_INFORMATION:
            module_path, class_name = MODEL_INFORMATION.get(model_name).rsplit(sep='.', maxsplit=1)
            return getattr(importlib.import_module(module_path), class_name), class_name
        else:
            raise ModelTypeNotFoundError(f'{model_name} is not a available model')

    def create_model_obj(self):
        try:
            model_class, class_name = self.get_model_class(self.model_name)
        except ModelTypeNotFoundError:
            raise ModelTypeNotFoundError(f'{self.model_name} is not a available model')

        if model_class:
            self.model = model_class(model_dir_name=self.model_path, feature=self.target_name)
        else:
            raise ValueError(f'model_name {self.model_name} is unknown')

        if isinstance(self.model, SupervisedModel):
            if not self.is_train:
                self.model.load()

        if isinstance(self.model, RuleBaseModel):
            if self.pattern:
                self.model.load(self.pattern)
            else:
                raise ParamterMissingError(f'patterns are missing')

        return self.model

    # @staticmethod
    # def trainable_model(type_attribute: str, target_attribute: str, **kwargs):
    #     return TrainableModelCreator().create_model(type_attribute, target_attribute, **kwargs)
    #
    # @staticmethod
    # def rule_based_model(type_attribute: str, target_attribute: str, **kwargs):
    #     return RuleBasedModelCreator().create_model(type_attribute, target_attribute, **kwargs)



