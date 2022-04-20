import csv
import os
from datetime import datetime
from typing import Dict, Any, List

from definition import SAVE_DOCUMENT_FOLDER
from settings import DatabaseConfig, TableName
from utils.data.data_download import pre_check
from utils.enum_config import DocumentTaskType, DocumentUploadStatus
from utils.exception_manager import SessionError
from workers.orm_core.base_operation import BaseOperation
from workers.preprocessing.preprocess_core import PreprocessWorker


class DocumentCRUD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO,
                 auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush,
                         echo=echo, **kwargs)
        self.dt = self.table_cls_dict.get(TableName.document_task)
        self.dd = self.table_cls_dict.get(TableName.document_dataset)
        self.dr = self.table_cls_dict.get(TableName.document_rules)
        self.du = self.table_cls_dict.get(TableName.document_upload)

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
            title=dataset.get('TITLE', ''),
            author=dataset.get('AUTHOR', ''),
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
                        content=item.get('data', None),
                        label=item.get('label', None),
                        rule_type=item.get('rule_type', None),
                        match_type=item.get('match_type', None),
                        task_id=task_id
                    )
                )
            return output_list
        else:
            for item in bulk_list:
                output_list.append(
                    self.dd(
                        title=item.get('title', ''),
                        author=item.get('author', ''),
                        s_id=item.get('s_id', ''),
                        s_area_id=item.get('s_area_id', ''),
                        content=item.get('data', None),
                        dataset_type=item.get('dataset_type', None),
                        label=item.get('label', None),
                        post_time=item.get('post_time', None),
                        task_id=task_id
                    )
                )
            return output_list

    def bulk_create(self, task_id: str, task_type: str, bulk_list: List[dict]):
        if task_type.lower() == DocumentTaskType.MACHINE_LEARNING.value:
            self.rule_bulk_create(task_id=task_id, rules=bulk_list)
        elif task_type.lower() == DocumentTaskType.RULE.value:
            self.dataset_bulk_create(task_id=task_id, dataset=bulk_list)
        else:
            raise ValueError(f"Unknown task type {task_type}")

    def upload_file(self, task_id: str, overwrite: bool, file):
        filepath = os.path.join(SAVE_DOCUMENT_FOLDER, file.filename)
        try:
            with open(filepath, 'wb+') as file_object:
                file_object.write(file.file.read())
            self.import_file(
                filepath=filepath,
                task_id=task_id,
                overwrite=overwrite
            )
        except Exception as e:
            raise SessionError(e)
        finally:
            self.dispose()

    def write_csv(self, task_id: str):
        task = self.session.query(self.dt).get(task_id)
        filename = f'{task.name}.csv'
        filepath = pre_check(filename, parent_dir=SAVE_DOCUMENT_FOLDER)
        try:
            if task.task_type.lower() == DocumentTaskType.MACHINE_LEARNING.value:
                bulk_list = task.document_dataset_collection
                with open(filepath, 'w', encoding='utf-8') as f:
                    fieldnames = ['id', 'title', 'author', 's_id', 's_area_id', 'content',
                                  'post_time', 'label', 'document_type', 'task_id']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for data in bulk_list:
                        writer.writerow({
                            'id': data.id,
                            'title': data.title,
                            'author': data.author,
                            's_id': data.s_id,
                            's_area_id': data.s_area_id,
                            'content': data.content,
                            'post_time': data.post_time,
                            'label': data.label,
                            'document_type': data.document_type,
                            'task_id': data.task_id
                        })
            elif task.task_type.lower() == DocumentTaskType.RULE.value:
                bulk_list = task.document_rules_collection
                with open(filepath, 'w', encoding='utf-8') as f:
                    fieldnames = ['id', 'content', 'label', 'rule_type',
                                  'match_type', 'task_id']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for data in bulk_list:
                        writer.writerow({
                            'id': data.id,
                            'content': data.content,
                            'label': data.label,
                            'rule_type': data.rule_type,
                            'match_type': data.match_type,
                            'task_id': data.task_id
                        })
            else:
                raise ValueError(f"Unknown task type {task.task_type}")
        except Exception as e:
            error_message = f"task {task_id} failed to write file since {e}"
            raise SessionError(error_message)
        finally:
            self.dispose()

    def import_file(self, filepath: str, task_id: str, overwrite: bool):
        id_ = self.upload_task_create(
            filepath=filepath,
            task_id=task_id
        )
        try:
            task = self.task_retrieve(task_id=task_id)

            if overwrite:
                prev_set = self.get_collection(task_id=task_id,
                                               task_type=task.task_type)
                prev_set.delete()
                self.session.commit()

            csv_rows = PreprocessWorker.read_csv_file(filepath)
            self.bulk_create(
                task_id=task_id,
                task_type=task.task_type,
                bulk_list=csv_rows
            )
            update_status = self.session.query(self.du).get(id_)
            update_status.finish_time = datetime.now()
            update_status.status = DocumentUploadStatus.DONE.value
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            error_message = f'failed to import file since {e}'
            update_status = self.session.query(self.du).get(id_)
            update_status.error_message = error_message
            update_status.status = DocumentUploadStatus.FAILURE.value
            self.session.commit()
            raise SessionError(error_message)

    def get_collection(self, task_id: str, task_type: str):
        if task_type.lower() == DocumentTaskType.MACHINE_LEARNING.value:
            task_collection = self.session.query(self.dd).filter(
                self.dd.task_id == task_id
            )
        elif task_type.lower() == DocumentTaskType.RULE.value:
            task_collection = self.session.query(self.dr).filter(
                self.dr.task_id == task_id
            )
        else:
            raise ValueError(f"Unknown task type {task_type}")

        return task_collection

    def upload_task_create(self, filepath: str, task_id: str):
        try:
            temp_status = self.du(
                filepath=filepath,
                status=DocumentUploadStatus.PENDING.value,
                create_time=datetime.now(),
                task_id=task_id
            )
            self.session.add(temp_status)
            self.session.commit()
            return temp_status.id
        except Exception as e:
            self.session.rollback()
            error_message = f'failed to create upload task since {e}'
            raise SessionError(error_message)
