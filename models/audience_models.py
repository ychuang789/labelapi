from abc import ABC, abstractmethod
from typing import Iterable

from utils.helper import get_logger
from utils.input_example import InputExample
from utils.selections import ModelType

class AudienceModel(ABC):
    def __init__(self, name: str, model_type: ModelType,
                 logger_name: str = "AudienceModel",
                 verbose: bool = False):
        self.name = name
        self.model_type = model_type
        self.logger = get_logger(logger_name, verbose=verbose)

    @abstractmethod
    def load(self, label_patterns):
        pass

    @abstractmethod
    def predict(self, input_examples: Iterable[InputExample]):
        pass

