import uuid
from unittest import TestCase

from settings import LABEL
from utils.enum_config import PredictTarget, ModelType
from utils.label.run_label_task import read_from_dir
from workers.predicting.predict_core import PredictWorker

pattern = read_from_dir('keyword_model', 'author_name')
inv = {v: k for k, v in LABEL.items()}
patterns = [{inv.get(k): v} for i in pattern for k, v in i.items()]

# TODO: redo this part

class TestPredictWorker(TestCase):

    task_id = uuid.uuid1().hex
    input_schema = 'wh_backpackers'
    input_table = 'ts_page_content'
    predict_type = PredictTarget.AUTHOR.value
    start_time = '2020-01-01'
    end_time = '2020-02-01'
    model_job_lists = [10,11]
    kwargs = {
        'MODEL_TYPE': ModelType.KEYWORD_MODEL.value,
        'PREDICT_TYPE': PredictTarget.AUTHOR.value,
        'START_TIME': '2020-01-01',
        'END_TIME': '2021-02-01',
        'PATTERN': patterns,
        'INPUT_SCHEMA': 'wh_backpackers',
        'INPUT_TABLE': 'ts_page_content',
        'OUTPUT_SCHEMA': 'audience_result',
        'COUNTDOWN': 5,
        'QUEUE': 'queue1',
        'MODEL_JOB_LIST': [10, 11],
        'SITE_CONFIG': {'host': 'dc-data11.eland.com.tw',
                        'port': 3306,
                        'user': 'rd2',
                        'password': 'eland5678',
                        'db': 'wh_backpackers',
                        'charset': 'utf8mb4'}
    }

    def setUp(self) -> None:
        self.labeling_worker = PredictWorker(task_id=self.task_id, model_job_list=self.model_job_lists,
                                             input_schema=self.input_schema, input_table=self.input_table,
                                             predict_type=self.predict_type, start_time=self.start_time,
                                             end_time=self.end_time, site_connection_info=self.kwargs['SITE_CONFIG'],
                                             **self.kwargs)

    def test_label_data(self):
        self.labeling_worker.add_task_info()
        self.labeling_worker.run_task()

