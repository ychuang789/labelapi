import uuid
from unittest import TestCase

from utils.model_core import ModelingWorker
from utils.selections import ModelType, PredictTarget


class TestModelingWorker1(TestCase):
    model_name = ModelType.TERM_WEIGHT_MODEL.name
    predict_type = PredictTarget.CONTENT.name
    model_path = '3_term_weight_model'
    dataset_number = 1
    dataset_schema = 'audience-toolkit-django'
    model_info = {"model_path": model_path,}
    task_id = uuid.uuid1().hex

    def setUp(self) -> None:
        self.tw_model = ModelingWorker(model_name=self.model_name,
                                       predict_type=self.predict_type,
                                       dataset_number=self.dataset_number,
                                       dataset_schema=self.dataset_schema,
                                       **self.model_info)

    def test_run_task(self):
        self.tw_model.add_task_info(self.task_id, self.model_name,
                                    self.predict_type, self.model_info.get('model_path'))
        self.tw_model.run_task(self.task_id)

class TestModelingWorker2(TestCase):
    model_name = ModelType.RANDOM_FOREST_MODEL.name
    predict_type = PredictTarget.CONTENT.name
    model_path = '4_random_forest_model'
    dataset_number = 1
    dataset_schema = 'audience-toolkit-django'
    model_info = {"model_path": model_path,}
    task_id = uuid.uuid1().hex

    def setUp(self) -> None:
        self.rf_model = ModelingWorker(model_name=self.model_name,
                                       predict_type=self.predict_type,
                                       dataset_number=self.dataset_number,
                                       dataset_schema=self.dataset_schema,
                                       **self.model_info)

    def test_run_task(self):
        self.rf_model.add_task_info(self.task_id, self.model_name,
                                    self.predict_type, self.model_info.get('model_path'))
        self.rf_model.run_task(self.task_id)
