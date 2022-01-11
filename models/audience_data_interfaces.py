from abc import ABC, abstractmethod

from workers.modeling.preprocess_core import PreprocessWorker


class PreprocessInterface(ABC):
    def __init__(self, model_name: str, predict_type: str,
                 dataset_number: int, dataset_schema: str, logger_name: str = 'modeling',
                 verbose = False,  _preprocessor=None, **model_information):
        self.model_name = model_name
        self.predict_type = predict_type
        self.dataset_number = dataset_number
        self.dataset_schema = dataset_schema
        self.logger_name = logger_name
        self.verbose = verbose
        self._preprocessor = PreprocessWorker()

    @abstractmethod
    def data_preprocess(self, is_train: bool = True):
        pass
