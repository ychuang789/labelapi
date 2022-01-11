import uuid
from unittest import TestCase

from workers.modeling.model_core import ModelingWorker
from utils.selections import ModelType, PredictTarget, TWFeatureModel, KeywordMatchType

rules = {"色情": [("外送茶", KeywordMatchType.PARTIALLY)]}

class TestModelingWorker1(TestCase):
    model_name = ModelType.TERM_WEIGHT_MODEL.name
    predict_type = PredictTarget.CONTENT.name
    model_path = '0_term_weight_model'
    dataset_number = 1
    model_job_id = 0
    dataset_schema = 'audience-toolkit-django'
    model_info = {"model_path": model_path, "feature_model": TWFeatureModel.SGD.name}
    task_id = uuid.uuid1().hex


    def test_run_task(self):
        self.tw_model = ModelingWorker(model_name=self.model_name,
                                       predict_type=self.predict_type,
                                       dataset_number=self.dataset_number,
                                       dataset_schema=self.dataset_schema,
                                       **self.model_info)
        self.tw_model.run_task(self.task_id, self.model_job_id)


class TestModelingWorker2(TestCase):
    model_name = ModelType.TERM_WEIGHT_MODEL.name
    predict_type = PredictTarget.CONTENT.name
    model_path = '0_term_weight_model'
    dataset_schema = 'audience-toolkit-django'
    model_info = {"model_path": model_path,}
    dataset_number = 3
    model_job_id = 0
    # task_id = uuid.uuid1().hex

    def test_run_task(self):
        self.tw_model = ModelingWorker(model_name=self.model_name,
                                       predict_type=self.predict_type,
                                       dataset_number=self.dataset_number,
                                       dataset_schema=self.dataset_schema,
                                       **self.model_info)

        self.tw_model.eval_outer_test_data(self.model_job_id)


class TestModelingWorker3(TestCase):
    model_name = ModelType.KEYWORD_MODEL.name
    predict_type = PredictTarget.CONTENT.name
    model_path = '0_keyword_model'
    dataset_number = 3
    model_job_id = 10
    dataset_schema = 'audience-toolkit-django'
    model_info = {"model_path": model_path, "patterns": rules}
    task_id = uuid.uuid1().hex

    def test_run_task(self):
        self.kw_model = ModelingWorker(model_name=self.model_name,
                                       predict_type=self.predict_type,
                                       dataset_number=self.dataset_number,
                                       dataset_schema=self.dataset_schema,
                                       **self.model_info)

        self.kw_model.run_task(self.task_id, self.model_job_id)


class TestModelingWorker4(TestCase):
    model_name = ModelType.KEYWORD_MODEL.name
    predict_type = PredictTarget.CONTENT.name
    model_path = '0_keyword_model'
    dataset_number = 1
    dataset_schema = 'audience-toolkit-django'
    model_info = {"model_path": model_path, "patterns": rules}
    job_id = 10

    def test_ext_test(self):
        dataset_number = 3
        self.tw_model = ModelingWorker(model_name=self.model_name,
                                       predict_type=self.predict_type,
                                       dataset_number=dataset_number,
                                       dataset_schema=self.dataset_schema,
                                       **self.model_info)

        self.tw_model.eval_outer_test_data(self.job_id)
