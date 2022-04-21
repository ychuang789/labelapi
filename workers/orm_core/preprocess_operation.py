from typing import List

from settings import DatabaseConfig, TableName, MATCH_TYPE_DICT
from utils.exception_manager import DataMissingError
from workers.orm_core.base_operation import BaseOperation
from workers.orm_core.table_creator import FilterRules
from workers.preprocessing import preprocess_core


class PreprocessCRUD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO, auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush, echo=echo, **kwargs)
        self.filter_rules = self.table_cls_dict.get(TableName.filter_rule)
        self.filter_rule_task = self.table_cls_dict.get(TableName.filter_rule_task)

    def create_task(self, name, feature, model_name, create_time, filepath):
        new_task = self.filter_rule_task(
            label=name,
            feature=feature,
            model_name=model_name,
            create_time=create_time
        )
        try:
            self.session.add(new_task)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        self.bulk_add_filter_rules(task_pk=new_task.task_id, bulk_rules=preprocess_core.PreprocessWorker.read_csv_file(filepath))

    def get_task(self, task_pk: int):
        return self.session.query(self.filter_rule_task).get(task_pk)

    def update_task(self, task_pk: int, **kwargs):
        current_task = self.get_task(task_pk)
        if not current_task:
            raise DataMissingError(f"There is no data retrieve")
        try:
            for k, v in kwargs.items():
                if hasattr(current_task, str(k.lower())):
                    setattr(current_task, str(k.lower()), v)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            err_msg = f"Cannot update the task {task_pk} since {e}"
            current_task.error_message = err_msg
            self.session.commit()
            raise ValueError(err_msg)

    def delete_task(self, task_pk: int):
        current_task = self.get_task(task_pk)
        if not current_task:
            raise DataMissingError(f"There is no data retrieve")
        try:
            self.session.delete(current_task)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            err_msg = f"Cannot update the task {task_pk} since {e}"
            current_task.error_message = err_msg
            self.session.commit()
            raise ValueError(err_msg)

    def create_filter_rule(self, task_pk: int, content: str, rule_type: str, label: str, match_type: str):
        new_rule = self.filter_rules(
            content=content,
            rule_type=rule_type,
            label=label,
            match_type=match_type,
            task_id=task_pk
        )
        try:
            self.session.add(new_rule)
            self.session.commit()
            return new_rule.id
        except Exception as e:
            self.session.rollback()
            raise e

    def read_filter_rule(self, rule_pk: int):
        return self.session.query(self.filter_rules).get(rule_pk)

    def update_filter_rule(self, rule_pk: int, **kwargs):
        current_rule = self.read_filter_rule(rule_pk)
        if not current_rule:
            raise DataMissingError(f"There is no data retrieve")
        try:
            for k, v in kwargs.items():
                if hasattr(current_rule, str(k)):
                    setattr(current_rule, str(k), v)
            self.session.commit()
            return f"Successfully updated filter_rule {rule_pk}"
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Cannot update the filter rule {rule_pk} since {e}")

    def delete_filter_rule(self, rule_pk: int):
        current_rule = self.read_filter_rule(rule_pk)
        if not current_rule:
            raise DataMissingError(f"There is no data retrieve")
        try:
            self.session.delete(current_rule)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Cannot delete filter rule {rule_pk} since {e}")

    def bulk_add_filter_rules(self, task_pk: int, bulk_rules: List[dict]):
        current_task = self.get_task(task_pk)
        try:
            if current_task.filter_rule_collection:
                self.session.query(self.filter_rules).filter(self.filter_rules.task_id == task_pk).delete()
                self.session.commit()

            output_list = []
            for br in bulk_rules:
                output_list.append(FilterRules(
                    content=br['content'],
                    rule_type=br['rule_type'],
                    label=br['label'],
                    match_type=MATCH_TYPE_DICT.get(br['match_type'], br['match_type']),
                    task_id=task_pk
                ))
            self.session.bulk_save_objects(output_list)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            err_msg = f'Cannot bulk add filter rules since {e}'
            current_task.error_message = err_msg
            self.session.commit()
            raise ValueError(err_msg)

    def get_filter_rules_set(self, task_pk: int):
        current_task = self.get_task(task_pk)
        return current_task.filter_rule_collection


