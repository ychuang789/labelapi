from datetime import datetime
from typing import Dict, Any, List

from settings import DatabaseConfig, TableName
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
            description=kwargs.get('DESCRIPTION', None),
            task_type=kwargs.get('TASK_TYPE', None),
            is_multi_label=kwargs.get('IS_MULTI_LABEL', False),
            create_time=kwargs.get('CREATE_TIME', datetime.now()),
            update_time=None
        )
        try:
            self.session.add(temp_task)
            self.session.commit()
            return temp_task.task_id
        except Exception as e:
            error_message = f"failed to add data since {e}"
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

    def dataset_create(self, task_id: str, **dataset):
        temp_dataset = self.dd(
            title= dataset.get('TITLE', ''),
            author= dataset.get('AUTHOR', ''),
            s_id=dataset.get('S_ID', ''),
            s_area_id=dataset.get('S_AREA_ID', ''),
            content=dataset.get('CONTENT', None),
            dataset_type=dataset.get('DATASET_TYPE', None),
            label=dataset.get('LABEL', None),
            post_time=dataset.get('POST_TIME', None),
            task_id=task_id
        )
        try:
            self.session.add(temp_dataset)
            self.session.commit()
            return temp_dataset.id
        except Exception as e:
            error_message = f"task {task_id} failed to add dataset since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def dataset_render(self, task_id: str):
        render_dataset = self.session.query(self.dt).get(task_id).document_dataset_collection
        return render_dataset

    def dataset_update(self, task_id: str, dataset_id: int, **patch_data):
        temp_row = self.session.query(self.dd).get(dataset_id)
        try:
            for key, value in patch_data.items():
                if hasattr(temp_row, key.lower()):
                    setattr(temp_row, key.lower(), value)
            self.session.commit()
            return temp_row.dataset_id
        except Exception as e:
            error_message = f"task {task_id} failed to update row {dataset_id} since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def dataset_delete(self, task_id: str, dataset_id: int):
        temp_row = self.session.query(self.dd).get(dataset_id)
        try:
            self.session.delete(temp_row)
            self.session.commit()
        except Exception as e:
            error_message = f"task {task_id} failed to delete row {dataset_id} since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def dataset_truncate(self, task_id: str):
        temp_dataset = self.session.query(self.dd).fileter(self.dd.task_id == task_id)
        try:
            temp_dataset.delete()
            self.session.commit()
        except Exception as e:
            error_message = f"task {task_id} failed to truncate dataset since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def dataset_bulk_create(self, task_id: str, dataset: List[Dict[str, Any]]):
        try:
            self.session.bulk_save_objects(
                self.get_bulk_list_with_task_id(task_id, dataset, is_rule=False)
            )
            self.session.commit()
            return task_id
        except Exception as e:
            error_message = f"task {task_id} failed to bulk create dataset since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def rule_create(self, task_id: str, **rule):
        temp_rule = self.dr(
            content=rule.get('CONTENT', None),
            label=rule.get('LABEL', None),
            rule_type=rule.get('RULE_TYPE', None),
            match_type=rule.get('MATCH_TYPE', None),
            task_id=task_id
        )
        try:
            self.session.add(temp_rule)
            self.session.commit()
            return temp_rule.id
        except Exception as e:
            error_message = f"task {task_id} failed to add rule since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def rule_render(self, task_id: str):
        render_rules = self.session.query(self.dt).get(task_id).document_rules_collection
        return render_rules

    def rule_update(self, task_id: str, rule_id: int, **patch_data):
        temp_row = self.session.query(self.dr).get(rule_id)
        try:
            for key, value in patch_data.items():
                if hasattr(temp_row, key.lower()):
                    setattr(temp_row, key.lower(), value)
            self.session.commit()
            return temp_row.rule_id
        except Exception as e:
            error_message = f"task {task_id} failed to update row {rule_id} since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def rule_delete(self, task_id: str, rule_id: int):
        temp_row = self.session.query(self.dr).get(rule_id)
        try:
            self.session.delete(temp_row)
            self.session.commit()
        except Exception as e:
            error_message = f"task {task_id} failed to delete row {rule_id} since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def rule_truncate(self, task_id: str):
        temp_rules = self.session.query(self.dr).fileter(self.dr.task_id == task_id)
        try:
            temp_rules.delete()
            self.session.commit()
        except Exception as e:
            error_message = f"task {task_id} failed to truncate rules since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def rule_bulk_create(self, task_id: str, rules: List[Dict[str, Any]]):
        try:
            self.session.bulk_save_objects(
                self.get_bulk_list_with_task_id(task_id, rules, is_rule=True)
            )
            self.session.commit()
            return task_id
        except Exception as e:
            error_message = f"task {task_id} failed to bulk create rules since {e}"
            self.session.rollback()
            raise SessionError(error_message)

    def get_bulk_list_with_task_id(self, task_id: str, bulk_list: List[Dict[str, Any]],
                                   is_rule: bool):
        output_list = []
        if is_rule:
            for item in bulk_list:
                output_list.append(
                    self.dr(
                        content=item.get('CONTENT', None),
                        label=item.get('LABEL', None),
                        rule_type=item.get('RULE_TYPE', None),
                        match_type=item.get('MATCH_TYPE', None),
                        task_id=task_id
                    )
                )
            return output_list
        else:
            for item in bulk_list:
                output_list.append(
                    self.dd(
                        title=item.get('TITLE', ''),
                        author=item.get('AUTHOR', ''),
                        s_id=item.get('S_ID', ''),
                        s_area_id=item.get('S_AREA_ID', ''),
                        content=item.get('CONTENT', None),
                        dataset_type=item.get('DATASET_TYPE', None),
                        label=item.get('LABEL', None),
                        post_time=item.get('POST_TIME', None),
                        task_id=task_id
                    )
                )
            return output_list


