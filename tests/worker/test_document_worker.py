from datetime import datetime
from unittest import TestCase, TestLoader

from workers.orm_core.document_operation import DocumentCRUD

TestLoader.sortTestMethodsUsing = lambda *args: -1

# task
fake_task_id_1 = '83b02587c13511ec8e3e04ea56825bad'
create_time = datetime.now()
fake_task_data_1 = {
    "NAME": "testing_document_task",
    "TASK_TYPE": "rule_task",
    "IS_MULTI_LABEL": True,
    "CREATE_TIME": create_time,
}
fake_patch_task = {'IS_MULTI_LABEL': False, 'DESCRIPTION': 'YOLO'}

# dataset
fake_dataset_id = 2
fake_dataset = {
    "CONTENT": "This is for testing",
    "LABEL": "TEST",
    "DATASET_TYPE": 'train'
}
fake_patch_dataset = {
    "DATASET_TYPE": 'test'
}

# rule
fake_rule_id = 1
fake_rules = {
    "CONTENT": "This is for testing",
    "LABEL": "TEST",
    "RULE_TYPE": "regex",
    "MATCH_TYPE": "partially"
}
fake_patch_rules = {
    "RULE_TYPE": "keyword",
    "MATCH_TYPE": "exactly"
}


class TestDocumentTaskC(TestCase):
    task_id = fake_task_id_1
    task_data = fake_task_data_1

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_task_create(self):
        output_task = self.worker.task_create(
            task_id=self.task_id, **self.task_data
        )
        self.assertEqual(output_task.task_id, self.task_id)


class TestDocumentTaskR(TestCase):
    task_id = fake_task_id_1

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_task_retrieve(self):
        task = self.worker.task_retrieve(task_id=self.task_id)
        self.assertEqual(task.is_multi_label, True)

    def test_task_render(self):
        tasks = self.worker.task_render()
        self.assertIsInstance(tasks, list)


class TestDocumentTaskU(TestCase):
    task_id = fake_task_id_1
    patch_data = fake_patch_task
    create_time = create_time

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_task_update(self):
        task = self.worker.task_update(
            task_id=self.task_id, **self.patch_data
        )
        self.assertNotEqual(task.update_time, self.create_time)
        self.assertEqual(task.is_multi_label, False)


class TestDocumentTaskD(TestCase):
    task_id = fake_task_id_1

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_task_delete(self):
        self.worker.task_delete(task_id=self.task_id)
        output = self.worker.task_retrieve(task_id=self.task_id)
        self.assertEqual(output, None)


class TestDatasetC(TestCase):
    task_id = fake_task_id_1
    dataset = fake_dataset

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_dataset_create(self):
        dataset = self.worker.dataset_create(
            task_id=self.task_id,
            **self.dataset
        )
        self.assertEqual(dataset.dataset_type, 'train')


class TestDatasetU(TestCase):
    task_id = fake_task_id_1
    patch_data = fake_patch_dataset
    dataset_id = fake_dataset_id

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_dataset_update(self):
        dataset = self.worker.dataset_update(
            task_id=self.task_id,
            dataset_id=self.dataset_id,
            **self.patch_data
        )
        self.assertEqual(dataset.dataset_type, 'test')


class TestDatasetRD(TestCase):
    task_id = fake_task_id_1
    dataset_id = fake_dataset_id

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_dataset_render_delete(self):
        render_list_1 = self.worker.dataset_render(
            task_id=self.task_id
        )
        self.assertNotEqual(len(render_list_1), 0)

        self.worker.dataset_delete(
            task_id=self.task_id,
            dataset_id=self.dataset_id
        )
        render_list_2 =self.worker.dataset_render(
            task_id=self.task_id
        )
        self.assertEqual(len(render_list_2), 0)


class TestRuleC(TestCase):
    task_id = fake_task_id_1
    dataset = fake_rules

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_dataset_create(self):
        dataset = self.worker.rule_create(
            task_id=self.task_id,
            **self.dataset
        )
        self.assertEqual(dataset.match_type, 'partially')


class TestRuleU(TestCase):
    task_id = fake_task_id_1
    patch_data = fake_patch_rules
    rule_id = fake_rule_id

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_dataset_update(self):
        dataset = self.worker.rule_update(
            task_id=self.task_id,
            rule_id=self.rule_id,
            **self.patch_data
        )
        self.assertEqual(dataset.match_type, 'exactly')


class TestRuleRD(TestCase):
    task_id = fake_task_id_1
    rule_id = fake_rule_id

    def setUp(self) -> None:
        self.worker = DocumentCRUD()

    def tearDown(self) -> None:
        self.worker.dispose()

    def test_dataset_render_delete(self):
        render_list_1 = self.worker.rule_render(
            task_id=self.task_id
        )
        self.assertNotEqual(len(render_list_1), 0)

        self.worker.rule_delete(
            task_id=self.task_id,
            rule_id=self.rule_id
        )
        render_list_2 =self.worker.rule_render(
            task_id=self.task_id
        )
        self.assertEqual(len(render_list_2), 0)
