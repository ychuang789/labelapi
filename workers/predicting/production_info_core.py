from typing import Dict

from settings import TableName
from utils.general_helper import get_logger
from utils.enum_config import PredictTaskStatus
from workers.orm_core.model_operation import ModelingCRUD


class TaskInfo(object):
    def __init__(self, task_id: str, table: str, row_count: int,logger: get_logger, orm_cls = None):
        self.task_id = task_id
        # self.schema = schema
        self.table = table
        self.row_count = row_count
        self.logger = logger
        self.orm_cls = orm_cls if orm_cls else ModelingCRUD()
        self.state = self.orm_cls.table_cls_dict.get(TableName.state)
        self.result = self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).first()

    def generate_output(self):

        _source_distinct_count = self.get_source_distinct_count()

        table_source_distinct_count = None
        if ',' in _source_distinct_count.get('uniq_source_author'):
            for idx, item in enumerate(_source_distinct_count.get('result').split(',')):
                if item == self.table:
                    table_source_distinct_count = int(_source_distinct_count.get('uniq_source_author').split(',')[idx])
                else:
                    pass
        else:
            table_source_distinct_count = int(_source_distinct_count.get('uniq_source_author'))

        assert table_source_distinct_count != None , 'table_source_distinct_count cannot be None'

        # generate rate of label for each output table
        rate_of_label = self._check_state_result_for_task_info()
        if rate_of_label:
            new_rate_of_label = rate_of_label + ',' + str(round((self.row_count / table_source_distinct_count)*100, 2))
        else:
            new_rate_of_label = str(round((self.row_count / table_source_distinct_count)*100, 2))

        # generate length of production for each output table
        length_prod_table = self._check_state_prod_length_for_task_info()
        if length_prod_table:
            new_length_prod_table = length_prod_table + ',' + str(self.row_count)
        else:
            new_length_prod_table = str(self.row_count)


        _task_info_statement = {
            self.state.prod_stat : PredictTaskStatus.PROD_SUCCESS.value,
            self.state.length_prod_table: new_length_prod_table,
            self.state.rate_of_label : new_rate_of_label
        }

        self.update_task_info(_task_info_statement)

    def update_task_info(self, kwargs: Dict):

        self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).update(kwargs)
        self.orm_cls.session.commit()


    def get_source_distinct_count(self):

        output = {c.label: getattr(self.result, c.label, None)
                  for c in self.result.__table__.columns
                  if c.label in ['result', 'uniq_source_author']}
        return output


    def _check_state_result_for_task_info(self):

        output = {c.label: getattr(self.result, c.label, None)
                  for c in self.result.__table__.columns
                  if c.label in ['result', 'rate_of_label']}

        if ',' in output.get('result'):
            return output.get('rate_of_label')
        else:
            return None

    def _check_state_prod_length_for_task_info(self):

        output = {c.label: getattr(self.result, c.label, None)
                  for c in self.result.__table__.columns
                  if c.label in ['result', 'length_prod_table']}

        if ',' in output.get('result'):
            return output.get('length_prod_table')
        else:
            return None
