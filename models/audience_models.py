
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List, Tuple

import settings
from utils.helper import get_logger
from utils.input_example import InputExample
from utils.model_core import PreprocessWorker

from utils.selections import ModelType, PredictTarget

MODEL_ROOT = Path(settings.MODEL_PATH_FIELD_DIRECTORY)

class RuleBaseModel(ABC):
    def __init__(self, name: str, model_type: ModelType,
                 case_sensitive: bool = False,
                 logger_name: str = "AudienceModel",
                 target: PredictTarget = PredictTarget.CONTENT,
                 verbose: bool = False):
        self.name = name
        self.model_type = model_type
        self.case_sensitive = case_sensitive
        self.target = target
        self.logger = get_logger(logger_name, verbose=verbose)

    @abstractmethod
    def load(self, label_patterns):
        """load the saved model or patterns"""
        pass

    @abstractmethod
    def predict(self, input_examples: Iterable[InputExample]):
        """predict the results of output, return labels and probs"""
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
        """predict the results of output, return labels and probs"""
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
        """load the model, make sure to do it before predict extral test set"""
        raise NotImplementedError


class PreprocessInterface(ABC):
    def __init__(self, _preprocessor=None):
        self._preprocessor = PreprocessWorker()

    @abstractmethod
    def data_preprocess(self):
        pass
