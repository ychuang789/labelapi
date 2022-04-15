from datetime import datetime
from typing import Dict, Any, List

from apis.input_class.documenting_input import DocumentRequest
from settings import DatabaseConfig, TableName
from utils.enum_config import DocumentType
from utils.exception_manager import SessionError
from workers.orm_core.base_operation import BaseOperation


class DocumentCRUD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO,
                 auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush,
                         echo=echo, **kwargs)
        self.dt = self.table_cls_dict.get(TableName.document_task)
        self.dd = self.table_cls_dict.get(TableName.document_dataset)
        self.dr = self.table_cls_dict.get(TableName.document_rules)

    def task_create(self, task_id: str, **kwargs):
        temp_task = self.dt(
            task_id=task_id,
            description=kwargs.get('description', None),
            is_multi_label=kwargs.get('is_multi_label', False),
            create_time=kwargs.get('create_time', datetime.now()),
            update_time=None
        )
        try:
            self.session.add(temp_task)
            self.session.commit()
            return temp_task.task_id
        except Exception as e:
            error_message = f"failed to session add data since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def task_update(self, task_id: str, **patch_data):
        temp_task = self.session.query(self.dt).get(task_id)
        try:
            for key, value in patch_data.items():
                if hasattr(temp_task, key.lower()):
                    setattr(temp_task, key.lower(), value)
            self.session.commit()
            return temp_task.task_id
        except Exception as e:
            error_message = f"failed to update task {task_id} since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def task_render(self):
        return self.session.query(self.dt).all()

    def task_retrieve(self, task_id: str):
        return self.session.query(self.dt).get(task_id)

    def task_delete(self, task_id: str):
        temp_task = self.task_retrieve(task_id)
        try:
            self.session.delete(temp_task)
            self.session.commit()
        except Exception as e:
            error_message = f"failed to delete task {task_id} since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def dataset_create(self, task_id: str, dataset: Dict[str, Any]):
        temp_dataset = self
        pass

    def dataset_render(self, task_id: str):
        pass

    def dataset_update(self, task_id: str, dataset_id: int):
        pass

    def dataset_delete(self, task_id: str, dataset_id: int):
        pass

    def dataset_delete_all(self, task_id: str, document_type: DocumentType = None):
        pass

    def dataset_bulk_create(self, task_id: str, dataset: List[Dict[str, Any]]):
        pass

