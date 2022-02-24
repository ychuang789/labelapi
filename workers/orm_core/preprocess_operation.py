from typing import List

from settings import DatabaseConfig, TableName
from utils.exception_manager import DataMissingError
from workers.orm_core.base_operation import BaseOperation


class PreprocessCURD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO, auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush, echo=echo, **kwargs)
        self.filter_rules = self.table_cls_dict.get(TableName.filter_rules)

    def create_filter_rule(self, content: str, rule_type: str, label: str, match_type: str):
        new_rule = self.filter_rules(
            content=content,
            rule_type=rule_type,
            label=label,
            match_type=match_type
        )
        try:
            self.session.add(new_rule)
            self.session.commit()
            return new_rule.id
        except Exception as e:
            self.session.rollback()
            raise e

    def read_filter_rule(self, pk):
        return self.session.query(self.filter_rules).get(pk)

    def update_filter_rule(self, pk, **kwargs):
        current_rule = self.read_filter_rule(pk)
        if not current_rule:
            raise DataMissingError(f"There is no data retrieve")
        try:
            for k, v in kwargs.items():
                if hasattr(current_rule, str(k)):
                    setattr(current_rule, str(k), v)
            self.session.commit()
            return f"Successfully updated filter_rule {pk}"
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Cannot update the filter rule {pk} since {e}")

    def delete_filter_rule(self, pk):
        current_rule = self.read_filter_rule(pk)
        if not current_rule:
            raise DataMissingError(f"There is no data retrieve")
        try:
            self.session.delete(current_rule)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Cannot delete filter rule {pk} since {e}")

    def bulk_add_filter_rules(self, bulk_rules: List[dict]):
        self.delete_all_filter_rules()
        try:
            output_list = []
            for br in bulk_rules:
                output_list.append(self.filter_rules(
                    content=br['content'],
                    rule_type=br['rule_type'],
                    label=br['label'],
                    match_type=br['match_type'])
                )
            self.session.bulk_save_objects(output_list)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise ValueError(f'Cannot bulk add filter rules since {e}')

    def get_all_filter_rules(self):
        return self.session.query(self.filter_rules).all()

    def delete_all_filter_rules(self):
        current_set = self.session.query(self.filter_rules).all()
        if not current_set:
            raise DataMissingError(f"There is no data retrieve")
        try:
            self.session.delete(current_set)
            self.session.commit()
            return f"Successfully delete all filter rules"
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Cannot delete all filter rules since {e}")
