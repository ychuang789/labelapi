from typing import Dict
from utils.database_core import connect_database, get_label_source_from_state, \
    check_state_result_for_task_info, check_state_prod_length_for_task_info
from utils.helper import get_logger
from utils.selections import TableRecord, PredictingProgressStatus
from workers.orm_core import ORMWorker


class TaskInfo(object):
    def __init__(self, task_id: str, table: str, row_count: int,logger: get_logger, orm_cls = None):
        self.task_id = task_id
        # self.schema = schema
        self.table = table
        self.row_count = row_count
        self.logger = logger
        self.orm_cls = orm_cls if orm_cls else ORMWorker()
        self.state = self.orm_cls.table_cls_dict.get(TableRecord.state.value)
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
            self.state.prod_stat : PredictingProgressStatus.PROD_SUCCESS.value,
            self.state.length_prod_table: new_length_prod_table,
            self.state.rate_of_label : new_rate_of_label
        }

        self.update_task_info(_task_info_statement)

    def update_task_info(self, kwargs: Dict):

        self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).update(kwargs)
        self.orm_cls.session.commit()

        # task_id = kwargs.get('task_id')
        # # input_data_size = kwargs.get('input_data_size')
        # length_prod_table = kwargs.get('length_prod_table')
        # # max_memory_usage = kwargs.get('max_memory_usage')
        # # run_time = kwargs.get('run_time')
        # rate_of_label = kwargs.get('rate_of_label')
        #
        #
        # update_sql = f'UPDATE state ' \
        #              f'SET prod_stat = "finish", ' \
        #              f'length_prod_table = "{length_prod_table}", ' \
        #              f'rate_of_label = "{rate_of_label}" ' \
        #              f'where task_id = "{task_id}"'
        #
        # try:
        #     _connection = connect_database(schema, output=True)
        #     cursor = _connection.cursor()
        #     cursor.execute(update_sql)
        #     _connection.commit()
        #     _connection.close()
        #     logger.info(f'successfully write into table state.')
        #
        # except Exception as e:
        #     logger.error(e)
        #     raise e

    def get_source_distinct_count(self):

        output = {c.name: getattr(self.result, c.name, None)
                  for c in self.result.__table__.columns
                  if c.name in ['result', 'uniq_source_author']}
        return output

        # q = f"""select result,uniq_source_author from state where task_id = "{task_id}";"""
        #
        # try:
        #     _connection = connect_database(schema, output=True)
        #     cursor = _connection.cursor()
        #     cursor.execute(q)
        #     source_distinct_count_str_wiht_result = cursor.fetchone()
        #     _connection.close()
        #     logger.info(f'successfully get uniq_source_author number from table state.')
        #
        # except Exception as e:
        #     logger.error(e)
        #     raise e
        #
        # return source_distinct_count_str_wiht_result

    def _check_state_result_for_task_info(self):

        output = {c.name: getattr(self.result, c.name, None)
                  for c in self.result.__table__.columns
                  if c.name in ['result', 'rate_of_label']}

        if ',' in output.get('result'):
            return output.get('rate_of_label')
        else:
            return None

    def _check_state_prod_length_for_task_info(self):

        output = {c.name: getattr(self.result, c.name, None)
                  for c in self.result.__table__.columns
                  if c.name in ['result', 'length_prod_table']}

        if ',' in output.get('result'):
            return output.get('length_prod_table')
        else:
            return None
