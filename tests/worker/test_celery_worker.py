import uuid
from unittest import TestCase

import pandas as pd
from celery.result import AsyncResult

from celery_worker import celery_app, label_data


query = f"SELECT * FROM predicting_jobs_predictingresult " \
        f"WHERE applied_feature='author' " \
        f"AND created_at >= '2021-01-01 00:00:00' " \
        f"AND created_at <= '2021-12-31 23:59:59' " \
        f"LIMIT 1000"

pattern = pd.read_pickle('rules/keyword')


# before the unit test, make sure the worker is running
class TestCeleryWorker(TestCase):




    def put_task(self):
        result = label_data.apply_async((uuid.uuid1().hex, query, pattern, model_type, predict_type))


