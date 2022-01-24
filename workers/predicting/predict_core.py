from datetime import datetime
from typing import Dict, List, Any, Union
import pandas as pd

from settings import DatabaseConfig, SOURCE, LABEL, TableName
from utils.data.data_cleaning import run_cleaning
from utils.database.database_helper import get_batch_by_timedelta, create_table
from utils.data.input_example import InputExample
from utils.enum_config import PredictTaskStatus, NATag
from utils.general_helper import get_logger
from workers.modeling.model_core import ModelingWorker
from workers.orm_core.predict_operation import PredictingCRUD
from workers.predicting.production_core import TaskGenerateOutput
from workers.predicting.production_info_core import TaskInfo


class PredictWorker:
    def __init__(self, task_id: str, input_schema: str, input_table: str, start_time: str,
                 end_time: str, model_job_list: List[int], site_connection_info: Dict[str, Union[str, int]] = None,
                 logger_name='label_data', orm_cls: PredictingCRUD = None, verbose=False, **kwargs):
        self.task_id = task_id
        self.logger = get_logger(logger_name, verbose=verbose)
        self.model_job_list = model_job_list
        self.input_schema = input_schema
        self.input_table = input_table
        self.start_date = datetime.strptime(start_time, "%Y-%m-%dT00:00:00")
        self.end_date = datetime.strptime(end_time, "%Y-%m-%dT00:00:00")
        self.site_connection_info: Dict = site_connection_info if site_connection_info else None
        self.task_info: Dict[str, Any] = kwargs
        self.table_dict = {}
        self.count = 0
        self.row_number = 0
        self.start_time = datetime.now()
        self.orm_cls = orm_cls if orm_cls else PredictingCRUD(echo=verbose, pool_size=0, max_overflow=-1)
        self.state = self.orm_cls.table_cls_dict.get(TableName.state)
        self.model_information, self.model_type = self.get_jobs_ids()
        self.predict_type = [i.feature.lower() for i in self.model_information]
        self.model_worker_list = self.get_model_list()

    def run_task(self):

        if not self.break_checker():
            return

        self.batch_process()

        change_status = {
            self.state.stat: PredictTaskStatus.SUCCESS.value,
            self.state.result: ','.join(self.table_dict.keys()),
            self.state.length_receive_table: self.count,
            self.state.length_output_table: self.row_number,
            self.state.uniq_source_author: ','.join([str(len(i)) for i in self.table_dict.values()]),
            self.state.run_time: (datetime.now() - self.start_time).total_seconds() / 60

        }
        self._update_state(change_status)
        self.logger.info(
            f'task {self.task_id} {self.input_schema}.{self.input_table} done.')

        if not self.break_checker():
            return

        if len(list(self.table_dict.keys())) == 0:
            change_status = {
                self.state.prod_stat: PredictTaskStatus.PROD_NODATA.value
            }
            self._update_state(change_status)
            return

        self.data_generator(list(self.table_dict.keys()))

    def batch_process(self):
        for idx, elements in enumerate(get_batch_by_timedelta(schema=self.input_schema,
                                                              predict_type=self.predict_type,
                                                              table=self.input_table,
                                                              begin_date=self.start_date,
                                                              last_date=self.end_date,
                                                              site_input=self.site_connection_info)):

            self.logger.info(
                f'Start {self.task_id} {self.input_schema}.{self.input_table}_batch_{idx} ...')

            element, date_checkpoint = elements

            if isinstance(element, str):
                change_status = {
                    self.state.stat: PredictTaskStatus.FAILURE.value,
                    self.state.check_point: date_checkpoint,
                    self.state.error_message: element
                }
                self._update_state(change_status)
                raise

            if not self.break_checker():
                return

            if element.empty:
                continue

            self.count += len(element)

            try:
                _output, row_num = self.data_labeler(element)
                self.row_number += row_num

                for k, v in _output.items():
                    if self.table_dict.get(k):
                        self.table_dict[k] = self.table_dict.get(k).union(v)
                    else:
                        self.table_dict.update({k: v})

                if self.table_dict:
                    change_status = {
                        self.state.result: ','.join(self.table_dict.keys()),
                    }
                    self._update_state(change_status)

                self.logger.info(f'task {self.task_id} {self.input_schema}.'
                                 f'{self.input_table}_batch_{idx} finished labeling...')

            except Exception as e:
                change_status = {
                    self.state.stat: PredictTaskStatus.FAILURE.value,
                    self.state.check_point: date_checkpoint,
                    self.state.error_message: e
                }
                self._update_state(change_status)

                err_msg = f'task {self.task_id} failed at {self.input_schema}.' \
                          f'{self.input_table}_batch_{idx}, additional error message {e}'
                self.logger.error(err_msg)
                raise e

    def data_labeler(self, df):

        start = datetime.now()
        self.logger.info(f'start labeling at {start} ...')
        df = self.predicting_output(df)

        _df_output = df[['id', 'task_id', 'source_author', 'create_time',
                         'panel', 'field_content', 'match_content', 'match_meta']]

        df_output = _df_output.loc[(_df_output['panel'] != '') & (_df_output['panel'] != NATag.na_tag.value)]

        self.logger.info(f'write the output into database ...')

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

        return result_table_dict, output_number_row

    def data_generator(self, output_table):
        """generate the production data with validation information"""
        for tb in output_table:
            self.logger.info(f'start generating output for table {tb}...')

            generate_production = TaskGenerateOutput(task_id=self.task_id, schema=DatabaseConfig.OUTPUT_SCHEMA,
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
            self.logger.info(
                f'total time for {self.task_id}: {tb} is {(datetime.now() - self.start_time).total_seconds() / 60} minutes')

        self.logger.info(f'finish task {self.task_id} generate_production, total time: '
                         f'{(datetime.now() - self.start_time).total_seconds() / 60} minutes')

    def predicting_output(self, dataframe):
        if self.model_information:
            output_df = pd.DataFrame(columns=list(dataframe.columns) + ['panel', 'match_content', 'match_meta', ])
            for _model_information, model_worker in zip(self.model_information, self.model_worker_list):
                df = dataframe.copy()

                try:

                    temp_list_label, temp_list_meta = self.predict_output_process(model_worker=model_worker, df=df)

                    df['panel'] = temp_list_label
                    df['match_meta'] = temp_list_meta
                    df['match_meta'] = df['match_meta'].astype(str)

                    df['task_id'] = [self.task_id] * len(df)
                    df['match_content'] = df[_model_information.feature.lower()]

                    df.rename(columns={'post_time': 'create_time'}, inplace=True)
                    df['source_author'] = df['s_id'] + '_' + df['author']
                    df['field_content'] = df['s_id']

                    output_df = output_df.append(df)
                except Exception as e:
                    raise e
                finally:
                    model_worker.orm_cls.dispose()

            return output_df

        else:
            raise ValueError('Model job id is not set yet, no model reference')

    def predict_output_process(self, model_worker, df):
        temp_list_label = []
        temp_list_meta = []
        for i in range(len(df)):
            _input_data = InputExample(
                id_=df['id'].iloc[i],
                s_area_id=df['s_area_id'].iloc[i],
                author=df['author'].iloc[i],
                title=df['title'].iloc[i],
                content=df['content'].iloc[i],
                post_time=df['post_time'].iloc[i]
            )
            rs, prob = model_worker.model.predict([_input_data])

            if model_worker.model.__class__.__name__ == "TermWeightModel":
                if len(rs) == 1:
                    if len(rs[0]) == 1:
                        temp_list_label.append(rs[0][0])
                        temp_list_meta.append(prob)
                    else:
                        _tmp_val = 0
                        _tmp_ky = ''
                        prob_dict = prob[0]
                        if prob[0].get(NATag.na_tag.value):
                            prob_dict.pop(NATag.na_tag.value)
                        for k, v in prob[0].items():
                            if v[0][1] > _tmp_val:
                                _tmp_val = v[0][1]
                                _tmp_ky = k
                        temp_list_label.append(_tmp_ky)
                        temp_list_meta.append(prob)
            else:
                if rs:
                    if len(rs) == 1:
                        if isinstance(rs[0], str):
                            temp_list_label.append(rs[0])
                            temp_list_meta.append(prob)
                        else:
                            if len(rs[0]) == 1:
                                temp_list_label.append(rs[0][0])
                                temp_list_meta.append(prob)
                            else:
                                # TODO: 如果規則模型同時被貼到許多標籤，保留方法
                                # temp_list.append(rs[0][0])
                                _tmp_val = 0
                                _tmp_ky = ''
                                for j in prob[0]:
                                    if j[1] > _tmp_val:
                                        _tmp_val = j[1]
                                        _tmp_ky = j[0]
                                temp_list_label.append(_tmp_ky)
                                temp_list_meta.append(prob)
                else:
                    temp_list_label.append('')
                    temp_list_meta.append('')
        return temp_list_label, temp_list_meta

    def break_checker(self):
        record = self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).first()
        if record.stat == 'BREAK':
            self.logger.info(f"task {self.task_id} is abort by the external user")
            return False
        else:
            return True

    def get_jobs_ids(self):
        ms = self.orm_cls.table_cls_dict.get(TableName.model_status)
        result = []
        _model_type = []
        for i in self.model_job_list:
            record = self.orm_cls.session.query(ms).filter(ms.job_id == i).first()
            _model_type.append(record.model_name)
            # result.append({c.name: getattr(record, c.name, None) for c in record.__table__.columns})
            result.append(record)

        model_type = ','.join(set(_model_type))
        return result, model_type

    def get_model_list(self):
        _temp_model_list = []
        for model in self.model_information:

            info_dict = {'model_path': model.model_path}

            model_worker = ModelingWorker(
                job_id=model.job_id,
                model_name=model.model_name,
                predict_type=model.feature.lower(),
                **info_dict)
            model_worker.init_model(is_train=False)

            _temp_model_list.append(model_worker)

        return _temp_model_list

    def _update_state(self, _config_dict: Dict):
        self.orm_cls.session.query(self.state).filter(self.state.task_id == self.task_id).update(_config_dict)
        self.orm_cls.session.commit()

    def dispose(self):
        self.orm_cls.session.close()
        self.orm_cls.dispose()

    def add_task_info(self):
        self.orm_cls.session.add(self.state(
            task_id=self.task_id,
            stat=PredictTaskStatus.PENDING.value,
            model_type=self.model_type,
            predict_type=','.join(set(self.predict_type)) if isinstance(self.predict_type, list) else self.predict_type,
            date_range=f"{self.start_date.strftime('%Y-%m-%d')} - {self.end_date.strftime('%Y-%m-%d')}",
            target_schema=self.input_schema,
            create_time=datetime.now()
        ))
        self.orm_cls.session.commit()
