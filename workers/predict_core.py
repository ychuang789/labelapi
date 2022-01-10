from datetime import datetime
from typing import Dict, Optional, List

import pandas as pd
from sqlalchemy import create_engine

from settings import DatabaseConfig, SOURCE, LABEL
from utils.clean_up_result import run_cleaning
from utils.database_core import get_batch_by_timedelta, create_table
from utils.helper import get_logger
from utils.input_example import InputExample
from workers.model_core import ModelingWorker
from utils.selections import PredictTarget, TableRecord, PredictingProgressStatus
from workers.orm_core import ORMWorker
from workers.production_core import TaskGenerateOutput
from workers.production_info_core import TaskInfo


class PredictWorker():

    def __init__(self, task_id, model_job_list: List[int] = None, logger_name = 'label_data', orm_cls: ORMWorker = None,verbose = False, **kwargs):
        self.task_id = task_id
        self.logger = get_logger(logger_name, verbose=verbose)
        self.model_job_list = model_job_list
        self.start_date = datetime.strptime(kwargs.pop('START_TIME'), "%Y-%m-%dT%H:%M:%S")
        self.end_date = datetime.strptime(kwargs.pop('END_TIME'), "%Y-%m-%dT%H:%M:%S")
        self.site_connection_info: Dict = kwargs.pop('SITE_CONFIG') if kwargs.get('SITE_CONFIG') else None
        self.task_info = kwargs
        self.table_dict = {}
        self.count = 0
        self.row_number = 0
        self.start_time = datetime.now()
        # self.model_information = DBConnection.execute_query(query=QueryManager.get_model_job_ids(model_job_list),
        #                                                     single=True if len(model_job_list) == 1 else False,
        #                                                     **ConnectionConfigGenerator.rd2_database(DatabaseConfig.OUTPUT_SCHEMA))
        self.orm_cls = orm_cls if orm_cls else ORMWorker(echo=verbose, pool_size=0, max_overflow=-1)
        self.state = self.orm_cls.table_cls_dict.get(TableRecord.state.value)
        self.model_information = self.get_jobs_ids()

    def run_task(self):
        # TODO: refactor with orm
        if not self.break_checker():
            return

        for idx, elements in enumerate(get_batch_by_timedelta(self.task_info.get('INPUT_SCHEMA'),
                                                              self.task_info.get('PREDICT_TYPE'),
                                                              self.task_info.get('INPUT_TABLE'),
                                                              self.start_date,
                                                              self.end_date,
                                                              site_input=self.site_connection_info)):

            self.logger.info(f'Start {self.task_id} {self.task_info.get("INPUT_SCHEMA")}.{self.task_info.get("INPUT_TABLE")}_batch_{idx} ...')

            element, date_checkpoint = elements

            if isinstance(element, str):
                change_config = {
                    self.state.stat: PredictingProgressStatus.FAILURE.value,
                    self.state.check_point: date_checkpoint,
                    self.state.error_message: elements
                }
                self._update_state(change_config)
                # update2state(self.task_id, '', self.logger, schema=DatabaseConfig.OUTPUT_SCHEMA, success=False,
                #              check_point=date_checkpoint, error_message=elements)
                return

            if not self.break_checker():
                return

            if element.empty:
                continue

            # change the `author` back to `author_name` to fit the label modeling
            pred = "author_name" if self.task_info.get('PREDICT_TYPE') == "author" else self.task_info.get('PREDICT_TYPE')

            self.count += len(element)

            try:
                _output, row_num = self.data_labeler(element, pred, self.task_info.get('PATTERN'))

                self.row_number += row_num

                for k, v in _output.items():
                    if self.table_dict.get(k):
                        self.table_dict[k] = self.table_dict.get(k).union(v)
                    else:
                        self.table_dict.update({k: v})

                if self.table_dict:
                    change_config = {
                        self.state.result: ','.join(self.table_dict.keys()),
                    }
                    self._update_state(change_config)

                    # update2state_temp_result_table(self.task_id,
                    #                                DatabaseConfig.OUTPUT_SCHEMA,
                    #                                ','.join(self.table_dict.keys()),
                    #                                self.logger)

                self.logger.info(f'task {self.task_id} {self.task_info.get("INPUT_SCHEMA")}.'
                             f'{self.task_info.get("INPUT_TABLE")}_batch_{idx} finished labeling...')

            except Exception as e:
                change_config = {
                    self.state.stat: PredictingProgressStatus.FAILURE.value,
                    self.state.check_point: date_checkpoint,
                    self.state.error_message: e
                }
                self._update_state(change_config)

                # update2state(self.task_id, '', self.logger,
                #              schema=DatabaseConfig.OUTPUT_SCHEMA,
                #              success=False,
                #              check_point=date_checkpoint,
                #              error_message=e)

                err_msg = f'task {self.task_id} failed at {self.task_info.get("INPUT_SCHEMA")}.' \
                          f'{self.task_info.get("INPUT_TABLE")}_batch_{idx}, additional error message {e}'
                self.logger.error(err_msg)
                raise e

        change_config = {
            self.state.stat: PredictingProgressStatus.SUCCESS.value,
            self.state.result: ','.join(self.table_dict.keys()),
            self.state.length_receive_table: self.count,
            self.state.length_output_table: self.row_number,
            self.state.uniq_source_author: ','.join([str(len(i)) for i in self.table_dict.values()]),
            self.state.run_time: (datetime.now() - self.start_time).total_seconds() / 60

        }
        self._update_state(change_config)
        self.logger.info(
            f'task {self.task_id} {self.task_info.get("INPUT_SCHEMA")}.{self.task_info.get("INPUT_TABLE")} done.')
        # update2state(self.task_id, ','.join(self.table_dict.keys()), self.logger, self.count, self.row_number, finish_time,
        #              schema=DatabaseConfig.OUTPUT_SCHEMA,
        #              uniq_source_author=','.join([str(len(i)) for i in self.table_dict.values()]))

        if not self.break_checker():
            return

        if len(list(self.table_dict.keys())) == 0:
            change_config = {
                self.state.prod_stat: PredictingProgressStatus.PROD_NODATA.value
            }
            self._update_state(change_config)
            # update2state_nodata(self.task_id, DatabaseConfig.OUTPUT_SCHEMA, self.logger)
            return

        self.data_generator(list(self.table_dict.keys()))

    def data_labeler(self, df: pd.DataFrame, predict_type: str, pattern: Optional[List[Dict]] = None):

        model_info = {"patterns": pattern} if pattern else {}
        start = datetime.now()
        self.logger.info(f'start labeling at {start} ...')
        """predicting worker"""
        df = self.predicting_output(df, predict_type, **model_info)

        df.rename(columns={'post_time': 'create_time'}, inplace=True)
        df['source_author'] = df['s_id'] + '_' + df['author']
        df['field_content'] = df['s_id']
        if predict_type == PredictTarget.AUTHOR_NAME.value:
            df['match_content'] = df['author']
        else:
            df['match_content'] = df[predict_type]

        _df_output = df[['id', 'task_id', 'source_author', 'create_time',
                         'panel', 'field_content', 'match_content']]

        df_output = _df_output.loc[_df_output['panel'] != '']

        self.logger.info(f'write the output into database ...')

        # engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO, pool_size=0, max_overflow=-1).connect()
        # exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]

        exist_tables = self.orm_cls.show_tables()
        result_table_dict = {}
        output_number_row = 0

        for k, v in SOURCE.items():
            df_write = df_output[df_output['field_content'].isin(v)]

            # for calculating label rate
            temp_unique_source_author_total = set(_df_output[_df_output['field_content'].isin(v)]['source_author'])

            if df_write.empty:
                continue

            _df_write = run_cleaning(df_write)

            _df_write = _df_write.replace({"panel": LABEL})
            _df_write['panel'] = '/' + _df_write['panel'].astype(str)

            # _table_name= f'wh_panel_mapping_{k}'
            _table_name = k
            if _table_name not in exist_tables:
                create_table(_table_name, self.logger, schema=DatabaseConfig.OUTPUT_SCHEMA)

            try:
                _df_write.to_sql(name=_table_name, con=self.orm_cls.engine, if_exists='append', index=False)
                self.logger.info(f'successfully write data into {DatabaseConfig.OUTPUT_SCHEMA}.{_table_name}')

            except Exception as e:
                # _df_write.to_csv('debug.csv', index=False, encoding='utf-8-sig')
                self.logger.error(f'write dataframe to {DatabaseConfig.OUTPUT_SCHEMA}.{_table_name} failed!')
                raise ValueError(f'failed to write output into {DatabaseConfig.OUTPUT_SCHEMA}.{_table_name}... '
                                 f'additional error message {e}')
            # result_table_list.append(_table_name)
            result_table_dict.update({_table_name: temp_unique_source_author_total})

            output_number_row += len(_df_write)
        # engine.close()

        # return result_table_list, output_number_row
        return result_table_dict, output_number_row

    def data_generator(self, output_table):
        """generate the production data with validation information"""
        for tb in output_table:
            self.logger.info(f'start generating output for table {tb}...')

            generate_production = TaskGenerateOutput(task_id=self.task_id, schema=self.task_info.get('OUTPUT_SCHEMA'),
                                                     table=tb, logger=self.logger)
            _output_table_name, row_num = generate_production.clean()

            self.logger.info(f'finish generating output for table {tb}')
            self.logger.info(f'start generating task validation for table {tb} ...')

            task_info_obj = TaskInfo(task_id=self.task_id, table=tb, row_count=row_num, logger=self.logger)

            try:
                task_info_obj.generate_output()
            except Exception as e:
                raise e
            finally:
                task_info_obj.orm_cls.dispose()

            self.logger.info(f'finish calculating rate_of_label for table {tb}')
            self.logger.info(f'total time for {self.task_id}: {tb} is {(datetime.now() - self.start_time).total_seconds() / 60} minutes')

        self.logger.info(f'finish task {self.task_id} generate_production, total time: '
                     f'{(datetime.now() - self.start_time).total_seconds() / 60} minutes')

    def predicting_output(self, df, predict_type, **model_info):

        if self.model_information:

            output_df = pd.DataFrame(columns=list(df.columns))
            for idx, _model_information in enumerate(self.model_information):
                _model_info = model_info.get('patterns')[idx] if model_info.get('patterns') else None

                info_dict = {'model_path': _model_information.get('model_path'), 'patterns': _model_info}

                worker = ModelingWorker(model_name=_model_information.get('model_name'),
                                       predict_type=predict_type,
                                       **info_dict)
                worker.init_model(is_train=False)
                temp_list = []
                for i in range(len(df)):
                    _input_data = InputExample(
                        id_=df['id'].iloc[i],
                        s_area_id=df['s_area_id'].iloc[i],
                        author=df['author'].iloc[i],
                        title=df['title'].iloc[i],
                        content=df['content'].iloc[i],
                        post_time=df['post_time'].iloc[i]
                    )
                    rs, prob = worker.model.predict([_input_data], target=predict_type)

                    if rs:
                        if len(rs) == 1:
                            temp_list.append(rs[0][0])
                    else:
                        temp_list.append('')

                df['panel'] = temp_list
                df['task_id'] = [self.task_id for i in range(len(df))]

                output_df = output_df.append(df)

            return output_df

        else:
            raise ValueError('Model job id is not set yet, no model reference')

    def break_checker(self):
        record = self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).first()
        if record.stat == 'BREAK':
            self.logger.info(f"task {self.task_id} is abort by the external user")
            return False
        else:
            return True

        # if check_break_status(self.task_id) == 'BREAK':
        #     self.logger.info(f"task {self.task_id} is abort by the external user")
        #     return False
        # else:
        #     return True

    def get_jobs_ids(self):
        ms = self.orm_cls.table_cls_dict.get(TableRecord.model_status.value)
        result = []
        for i in self.model_job_list:
            record = self.orm_cls.session.query(ms).filter(ms.job_id == i).first()
            result.append({c.name: getattr(record, c.name, None) for c in record.__table__.columns})

        # connection = pymysql.connect(**ConnectionConfigGenerator.rd2_database("audience_result"))
        # cursor = connection.cursor()
        # cursor.execute(QueryManager.get_model_job_ids(self.model_job_list))
        # if len(self.model_job_list) <= 1:
        #     result = cursor.fetchone()
        # else:
        #     result = cursor.fetchall()
        # connection.close()
        return result

    def _update_state(self,_config_dict: Dict):
        self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).update(_config_dict)
        self.orm_cls.session.commit()

    def _dispose(self):
        self.orm_cls.session.close()
        self.orm_cls.dispose()
