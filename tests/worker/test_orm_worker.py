from unittest import TestCase

from settings import DatabaseConfig
from workers.orm_core.model_operation import ModelingCRUD


class TestModelORMWorker(TestCase):
    conn = DatabaseConfig.OUTPUT_ENGINE_INFO
    model_job_id = 0

    def setUp(self) -> None:
        self.orm_cls = ModelingCRUD(connection_info=self.conn)

    def test_status_changer(self):
        er = self.orm_cls.status_changer(task_id=self.model_job_id)
        self.assertIsInstance(er, str)

    def test_get_status(self):
        record = self.orm_cls.get_status(task_id=self.model_job_id)
        self.assertIsNotNone(record)

    def test_get_report(self):
        report = self.orm_cls.get_report(task_id=self.model_job_id)
        self.assertIsNotNone(report)

    def test_dispose(self):
        self.orm_cls.dispose()

