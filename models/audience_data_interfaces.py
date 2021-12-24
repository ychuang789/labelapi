from abc import ABC, abstractmethod

from utils.data_helper import PreprocessWorker


class PreprocessInterface(ABC):
    def __init__(self, _preprocessor=None):
        self._preprocessor = PreprocessWorker()

    @abstractmethod
    def data_preprocess(self):
        pass
