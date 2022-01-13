from unittest import TestCase

from settings import DatabaseConfig
from workers.orm_core.model_orm_core import ModelORM


class TestModelORMWorker(TestCase):
    conn = DatabaseConfig.OUTPUT_ENGINE_INFO
    model_job_id = 0

    def setUp(self) -> None:
        self.orm_cls = ModelORM(connection_info=self.conn)

    def test_status_changer(self):
        er = self.orm_cls.model_status_changer(model_job_id=self.model_job_id)
        self.assertIsInstance(er, str)

    def test_get_status(self):
        record = self.orm_cls.model_get_status(model_job_id=self.model_job_id)
        self.assertIsNotNone(record)

    def test_get_report(self):
        report = self.orm_cls.model_get_report(model_job_id=self.model_job_id)
        self.assertIsNotNone(report)

    def test_dispose(self):
        self.orm_cls.dispose()

