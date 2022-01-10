import uuid
from datetime import datetime
from unittest import TestCase

from settings import LABEL, DatabaseConfig
from utils.database_core import insert2state
from utils.helper import get_logger
from utils.run_label_task import read_from_dir
from workers.predict_core import PredictWorker

pattern = read_from_dir('keyword_model', 'author_name')
inv = {v: k for k, v in LABEL.items()}
patterns = [{inv.get(k): v} for i in pattern for k, v in i.items()]

class TestPredictWorker(TestCase):

    task_id = uuid.uuid1().hex
    kwargs = {
        'MODEL_TYPE': 'keyword_model',
        'PREDICT_TYPE': 'author',
        'START_TIME': '2020-01-01',
        'END_TIME': '2021-01-01',
        'PATTERN': patterns,
        'INPUT_SCHEMA': 'wh_backpackers',
        'INPUT_TABLE': 'ts_page_content',
        'OUTPUT_SCHEMA': 'audience_result',
        'COUNTDOWN': 5, 'QUEUE': 'queue1',
        'MODEL_JOB_LIST': [10, 11],
        'SITE_CONFIG': {'host': 'dc-data11.eland.com.tw',
                        'port': 3306,
                        'user': 'rd2',
                        'password': 'eland5678',
                        'db': 'wh_backpackers',
                        'charset': 'utf8mb4'}
    }

    def setUp(self):
        insert2state(self.task_id, 'pending', self.kwargs.get('MODEL_TYPE'), self.kwargs.get('PREDICT_TYPE'),
                     self.kwargs.get('date_range'), self.kwargs.get('INPUT_SCHEMA'), datetime.now(), "",
                     get_logger('label_data'), schema=DatabaseConfig.OUTPUT_SCHEMA)
        labeling_worker = PredictWorker(self.task_id, self.kwargs.pop('MODEL_JOB_LIST'), **self.kwargs)
        labeling_worker.run_task()
