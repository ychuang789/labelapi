from ast import literal_eval

from models.keyword_model import KeywordModel
from models.rf_model import RandomForestModel
from models.rule_model import RuleModel
from models.tw_model import TermWeightModel
from utils.selections import ModelType

class ModelTypeNotFound(Exception):
    pass

class ParamterMissingError(Exception):
    pass

class ModelCreator():

    def __init__(self):
        pass

    def __repr__(self):
        return 'Generate a corresponded model which user called'

    @staticmethod
    def create_model(type_attribute, **kwargs):

        if not hasattr(ModelType, type_attribute):
            raise ModelTypeNotFound(f'{type_attribute} is not in default ModelType')
        else:
            type_attribute = type_attribute.lower()

        if type_attribute == ModelType.KEYWORD_MODEL.value:
            keyword_patterns = kwargs.get('keyword_patterns')
            if not keyword_patterns:
                raise ParamterMissingError(f'keyword patterns')
            return KeywordModel(label_keywords=keyword_patterns)

        elif type_attribute == ModelType.RULE_MODEL.value:
            regex_patterns = kwargs.get('regex_patterns')
            if not regex_patterns:
                raise ParamterMissingError(f'regex patterns')
            return RuleModel(model_rules=regex_patterns)

        elif type_attribute == ModelType.RANDOM_FOREST_MODEL.value:
            model_path = kwargs.get('model_path')
            if not model_path:
                raise ParamterMissingError(f'model_path')
            return RandomForestModel(model_dir_name=model_path)

        elif type_attribute == ModelType.TERM_WEIGHT_MODEL.value:
            model_path = kwargs.get('model_path')
            if not model_path:
                raise ParamterMissingError(f'model_path')
            return TermWeightModel(model_dir_name=model_path)

        else:
            raise ModelTypeNotFound(f'{type_attribute} is unknown')



