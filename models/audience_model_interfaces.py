
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List, Tuple

import settings
from utils.general_helper import get_logger
from utils.data.input_example import InputExample

from utils.enum_config import ModelType, PredictTarget

MODEL_ROOT = Path(settings.MODEL_PATH_FIELD_DIRECTORY)

class RuleBaseModel(ABC):
    def __init__(self, name: str, model_dir_name: str, model_type: ModelType,
                 case_sensitive: bool = False,
                 logger_name: str = "AudienceModel",
                 feature: PredictTarget = PredictTarget.CONTENT,
                 verbose: bool = False):
        self.name = name
        self.model_dir_name = model_dir_name
        self.model_type = model_type
        self.case_sensitive = case_sensitive
        self.target = feature.value if isinstance(feature, PredictTarget) else feature
        self.logger = get_logger(logger_name, verbose=verbose)

    @abstractmethod
    def load(self, label_patterns):
        """load the saved model or patterns"""
        pass

    @abstractmethod
    def predict(self, input_examples: Iterable[InputExample]):
        """predicting the results of output, return labels and probs"""
        pass

    # @abstractmethod
    # def eval(self, examples: List[InputExample], y_true):
    #     """evaluate with validation set, return the report"""
    #     pass



class SupervisedModel(ABC):
    def __init__(self, model_dir_name: str, feature: PredictTarget = PredictTarget.CONTENT, na_tag=None, **kwargs):
        self.model = None
        self.model_dir_name = Path(model_dir_name)
        self.feature = feature if isinstance(feature, PredictTarget) else PredictTarget(feature)
        self.is_multi_label = True
        self.na_tag = na_tag

    @abstractmethod
    def fit(self, examples: Iterable[InputExample], y_true):
        """train the model"""
        raise NotImplementedError

    @abstractmethod
    def predict(self, examples: Iterable[InputExample]) -> List[Tuple[Tuple]]:
        """predicting the results of output, return labels and probs"""
        raise NotImplementedError

    @abstractmethod
    def eval(self, examples: Iterable[InputExample], y_true):
        """evaluate with validation set, return the report"""
        raise NotImplementedError

    @abstractmethod
    def save(self):
        """save the model"""
        raise NotImplementedError

    @abstractmethod
    def load(self):
        """load the model, make sure to do it before predicting extral test set"""
        raise NotImplementedError



