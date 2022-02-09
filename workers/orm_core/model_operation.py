from settings import DatabaseConfig, TableName
from utils.enum_config import ModelTaskStatus
from utils.exception_manager import UploadModelError
from workers.orm_core.base_operation import BaseOperation

class ModelingCRUD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO, auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush, echo=echo, **kwargs)
        self.ms = self.table_cls_dict.get(TableName.model_status)
        self.mr = self.table_cls_dict.get(TableName.model_report)
        self.rule = self.table_cls_dict.get(TableName.rules)
        self.upload_model = self.table_cls_dict.get(TableName.upload_model)
        self.eval_details = self.table_cls_dict.get(TableName.eval_details)

    def status_changer(self, task_id: str, status: ModelTaskStatus.BREAK = ModelTaskStatus.BREAK):
        err_msg = f'{task_id} {status.value} by the external user'
        try:
            self.session.query(self.ms).filter(self.ms.task_id == task_id).update({self.ms.training_status: status.value,
                                                                                   self.ms.error_message: err_msg})
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_record(self, task_id: str):
        try:
            record = self.session.query(self.ms).get(task_id)
            self.session.delete(record)
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise e

    def get_status(self, task_id: str):
        return self.orm_cls_to_dict(self.session.query(self.ms).get(task_id))

    def get_report(self, task_id: str):
        reports = self.session.query(self.mr).filter(self.mr.task_id == task_id).all()
        return [self.orm_cls_to_dict(r) for r in reports]

    def get_rules(self, task_id: str):
        return self.session.query(self.rule).filter(self.rule.task_id == task_id).all()

    def start_upload_model_to_table(self, task_id: str, upload_job_id: int, filename: str):
        temp_model = self.upload_model(
            filename=filename,
            status=ModelTaskStatus.STARTED.value,
            upload_job_id=upload_job_id,
            task_id=task_id
        )
        try:
            self.session.add(
                temp_model
            )
            self.session.commit()

            return temp_model.id
        except Exception as e:
            err_msg = f"failed to add record to upload_model since {e}"
            self.session.rollback()
            raise UploadModelError(err_msg)

    def get_upload_model_status(self, upload_job_id: int):
        obj = self.session.query(self.upload_model).filter(self.upload_model.upload_job_id == upload_job_id).one()
        return self.orm_cls_to_dict(obj)

    def get_eval_details(self, task_id: str, report_id: int, limit: int = None):
        if limit:
            obj = self.session.query(self.eval_details). \
                filter(self.eval_details.task_id == task_id,
                       self.eval_details.report_id == report_id).limit(limit).all()
        else:
            obj = self.session.query(self.eval_details).\
                filter(self.eval_details.task_id == task_id,
                       self.eval_details.report_id == report_id).all()

        return [self.orm_cls_to_dict(o) for o in obj]

    def get_eval_details_false_prediction(self, task_id: str, report_id: int, limit: int = None):
        if limit:
            obj = self.session.query(self.eval_details). \
                filter(self.eval_details.task_id == task_id,
                       self.eval_details.report_id == report_id,
                       self.eval_details.ground_truth != self.eval_details.predict_label).limit(limit).all()
        else:
            obj = self.session.query(self.eval_details). \
                filter(self.eval_details.task_id == task_id,
                       self.eval_details.report_id == report_id,
                       self.eval_details.ground_truth != self.eval_details.predict_label).all()

        return [self.orm_cls_to_dict(o) for o in obj]

    def get_eval_details_true_prediction(self, task_id: str, report_id: int, limit: int = None):
        if limit:
            obj = self.session.query(self.eval_details). \
                filter(self.eval_details.task_id == task_id,
                       self.eval_details.report_id == report_id,
                       self.eval_details.ground_truth == self.eval_details.predict_label).limit(limit).all()
        else:
            obj = self.session.query(self.eval_details). \
                filter(self.eval_details.task_id == task_id,
                       self.eval_details.report_id == report_id,
                       self.eval_details.ground_truth != self.eval_details.predict_label).all()

        return [self.orm_cls_to_dict(o) for o in obj]


