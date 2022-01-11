from settings import DatabaseConfig
from utils.selections import ModelTaskStatus, TableRecord
from workers.orm_core.orm_base import ORMWorker


class ModelORM(ORMWorker):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO, auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush, echo=echo, **kwargs)
        self.ms = self.table_cls_dict.get(TableRecord.model_status.value)
        self.mr = self.table_cls_dict.get(TableRecord.model_report.value)

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
            record = self.session.query(self.ms).filter(self.ms.job_id == model_job_id).first()
            self.session.delete(record)
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
        report = self.session.query(self.mr).filter(self.mr.task_id == record.task_id).all()

        return report



