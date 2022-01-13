from typing import List, Dict, Optional, Any

from sqlalchemy import desc

from settings import DatabaseConfig, TableName
from utils.database.database_helper import get_sample_query
from utils.enum_config import PredictTaskStatus
from workers.orm_core.base_operation import BaseOperation


class PredictingCRUD(BaseOperation):
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO, auto_flush=False, echo=False, **kwargs):
        super().__init__(connection_info=connection_info, auto_flush=auto_flush, echo=echo, **kwargs)
        self.st = self.table_cls_dict.get(TableName.state)

    def predict_tasks_list(self, limit_size: int = 10, page: Optional[int] = None) -> List[Dict[str, Any]]:
        query = self.session.query(self.st).order_by(desc(self.st.create_time)).limit(limit_size)

        if page:
            query = query.offset(page * limit_size)

        results = query.all()

        return [self.orm_cls_to_dict(r) for r in results]

    def predict_check_status(self, task_id: str) -> Dict[str, Any]:
        result = self.session.query(self.st).filter(self.st.task_id == task_id).first()
        return self.orm_cls_to_dict(result)

    def predict_sample_result(self, task_id: str, offset: int = 50) -> Optional[str]:
        result = self.session.query(self.st).filter(self.st.task_id == task_id).first()

        if not result.result or len(result.result) == 0:
            if result.prod_stat == PredictTaskStatus.PROD_NODATA.value:
                return PredictTaskStatus.PROD_NODATA.value
            else:
                return None

        q_list = [get_sample_query(_id=task_id, tablename=item, number=offset) for item in result.result.split(',')]
        query = ' UNION ALL '.join(q_list)

        return query

    def predict_abort_task(self, task_id):

        try:
            change_status = {self.st.stat: PredictTaskStatus.BREAK.value}
            self.session.query(self.st).filter(self.st.task_id == task_id).update(change_status)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
