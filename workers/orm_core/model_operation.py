from settings import DatabaseConfig, TableName
from utils.enum_config import ModelTaskStatus
from workers.orm_core.base_operation import BaseOperation

class ModelingCRUD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO, auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush, echo=echo, **kwargs)
        self.ms = self.table_cls_dict.get(TableName.model_status)
        self.mr = self.table_cls_dict.get(TableName.model_report)
        self.rule = self.table_cls_dict.get(TableName.rules)

    def model_status_changer(self, model_job_id: int, status: ModelTaskStatus.BREAK = ModelTaskStatus.BREAK):
        err_msg = f'{model_job_id} {status.value} by the external user'

        try:
            self.session.query(self.ms).filter(self.ms.job_id == model_job_id).update({self.ms.training_status: status.value,
                                                                         self.ms.error_message: err_msg})
            self.session.commit()
            return err_msg
        except Exception as e:
            self.session.rollback()
            raise e

    def model_delete_record(self, model_job_id: int):
        err_msg = f'{model_job_id} is deleted'

        try:
            record = self.session.query(self.ms).filter(self.ms.job_id == model_job_id).all()
            for r in record:
                self.session.delete(r)
                self.session.commit()
            return err_msg
        except Exception as e:
            self.session.rollback()
            raise e

    def model_get_status(self, model_job_id: int):
        record = self.session.query(self.ms).filter(self.ms.job_id == model_job_id).first()
        return record

    def model_get_report(self, model_job_id: int):
        record = self.session.query(self.ms).filter(self.ms.job_id == model_job_id).first()
        # get() vs first()
        return record.model_report_collection




