from unittest import TestCase

from settings import DatabaseConfig
from workers.orm_core.model_operation import ModelingCRUD
from workers.orm_core.preprocess_operation import PreprocessCRUD


class TestModelingCRUD(TestCase):
    conn = DatabaseConfig.OUTPUT_ENGINE_INFO
    task_id = 'e9c9c8898d6711eca20004ea56825bad'

    def setUp(self) -> None:
        self.orm_cls = ModelingCRUD(connection_info=self.conn)

    def test_status_changer(self):
        er = self.orm_cls.status_changer(task_id=self.task_id)
        self.assertIsInstance(er, str)

    def test_get_status(self):
        record = self.orm_cls.get_status(task_id=self.task_id)
        self.assertIsNotNone(record)

    def test_get_report(self):
        report = self.orm_cls.get_report(task_id=self.task_id)
        self.assertIsNotNone(report)

    def test_dispose(self):
        self.orm_cls.dispose()


class TestPreprocessCRUD(TestCase):
    conn = DatabaseConfig.OUTPUT_ENGINE_INFO
    task_id = 1

    def setUp(self) -> None:
        self.orm_cls = PreprocessCRUD(connection_info=self.conn)

    def test_get_task(self):
        result = self.orm_cls.get_task(self.task_id)
        self.assertIsNotNone(result)

    def test_get_filter_rules_set(self):
        result = self.orm_cls.get_filter_rules_set(self.task_id)
        self.assertIsNotNone(result)
