from typing import Union, List, Dict, Tuple

from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from settings import DatabaseConfig
from utils.model_table_creator import ModelStatus, ModelReport, TermWeights, Base
from utils.selections import ModelTaskStatus, ModelRecordTable


class ORMWorker():
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO,
                 auto_flush=False, echo=False):
        self.connection_info = connection_info
        self.base = Base
        self.engine = create_engine(self.connection_info, echo=echo)
        self.create_table_cls()
        self.session = Session(self.engine, autoflush=auto_flush)
        self.table_name_list = [item.value for item in ModelRecordTable]
        self.table_cls_dict = self.table_cls_maker(self.table_name_list)

    def dispose(self):
        self.close_session()
        self.engine.dispose()

    def __str__(self):
        return f"table class object : {','.join(list(self.table_cls_dict.keys()))}"

    def create_table_cls(self):
        inspector = inspect(self.engine)
        tables = [item.value for item in ModelRecordTable]
        show_table = inspector.get_table_names()
        if not set(tables).issubset(show_table):
            self.base.metadata.create_all(self.engine, checkfirst=True)
            # self.engine.dispose()

    def table_cls_maker(self, table_attr: Union[List[str]]) -> Dict:
        meta = MetaData()
        meta.reflect(self.engine, only=table_attr)
        Base = automap_base(metadata=meta)
        Base.prepare()
        # build table cls
        return {i: getattr(Base.classes, i) for i in table_attr}

        # if status_only:
        #     meta.reflect(self.engine, only=['model_status'])
        #     Base = automap_base(metadata=meta)
        #     Base.prepare()
        #
        #     # build table cls
        #     ms = Base.classes.model_status
        #     return ms
        # else:
        #     meta.reflect(self.engine, only=['model_status', 'model_report', 'term_weights'])
        #     Base = automap_base(metadata=meta)
        #     Base.prepare()
        #
        #     # build table cls
        #     ms = Base.classes.model_status
        #     mr = Base.classes.model_report
        #
        #     return ms, mr

    def status_changer(self, model_job_id: int, status: ModelTaskStatus.BREAK = ModelTaskStatus.BREAK):
        ms = self.table_cls_dict.get(ModelRecordTable.model_status.value)
        err_msg = f'{model_job_id} {status.value} by the external user'

        try:
            self.session.query(ms).filter(ms.job_id == model_job_id).update({ms.training_status: status.value,
                                                                         ms.error_message: err_msg})
            self.session.commit()
            return err_msg
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_record(self, model_job_id: int):
        ms = self.table_cls_dict.get(ModelRecordTable.model_status.value)
        err_msg = f'{model_job_id} delete by the external user'

        try:
            record = self.session.query(ms).filter(ms.job_id == model_job_id).first()
            self.session.delete(record)
            self.session.commit()
            return err_msg
        except Exception as e:
            self.session.rollback()
            raise e

    def get_status(self, model_job_id: int):
        ms = self.table_cls_dict.get(ModelRecordTable.model_status.value)
        record = self.session.query(ms).filter(ms.job_id == model_job_id).first()
        return record

    def get_report(self, model_job_id: int):
        ms = self.table_cls_dict.get(ModelRecordTable.model_status.value)
        mr = self.table_cls_dict.get(ModelRecordTable.model_report.value)

        record = self.session.query(ms).filter(ms.job_id == model_job_id).first()
        report = self.session.query(mr).filter(mr.task_id == record.task_id).all()

        return report

    def close_session(self):
        self.session.close()


