import json
from datetime import datetime

from celery import Celery
from sqlalchemy import create_engine

from settings import CeleryConfig, DatabaseInfo, CreateTaskRequestBody
from utils.database_core import scrap_data_to_df, update2state, get_data_by_batch
from utils.helper import get_logger
from utils.run_label_task import labeling

# create_db('save.db', CeleryConfig.sql_uri)

name = CeleryConfig.name
celery_app = Celery(name=name,
                    backend=CeleryConfig.backend,
                    broker=CeleryConfig.broker)

celery_app.conf.update(enable_utc=CeleryConfig.enable_utc)
celery_app.conf.update(timezone=CeleryConfig.timezone)
celery_app.conf.update(result_extended=True)
celery_app.conf.update(task_track_started=True)

@celery_app.task(name=f'{name}.label_data', track_started=True)
def label_data(task_id, schema, pattern, model_type, predict_type, **kwargs):
    start_time = datetime.now()
    _logger = get_logger('label_data')
    engine = create_engine(DatabaseInfo.input_engine_info)
    _target_table = CreateTaskRequestBody().target_table
    count = engine.execute(f"SELECT COUNT(*) FROM {_target_table}").fetchone()[0]

    table_set = set()
    for idx, element in enumerate(get_data_by_batch(predict_type ,count, CeleryConfig.batch_size,
                                                    schema, _target_table, **kwargs)):

        # df = scrap_data_to_df(_logger, query, schema=schema)
        df = element

        try:
            _output = labeling(task_id, df, model_type, predict_type, pattern, _logger, to_database=True)
            for i in _output:
                table_set.add(i)

        except Exception as e:
            update2state(task_id, '', _logger, schema=DatabaseInfo.output_schema, seccess=False)

            err_msg = f'task {task_id} failed at {_target_table}_batch_{idx}, additional error message {e}'
            _logger.error(err_msg)
            raise err_msg

    update2state(task_id, ','.join(table_set), _logger, schema=DatabaseInfo.output_schema)

    finish_time = datetime.now()
    _logger.info(f'the time of {task_id}:{schema}.{_target_table}is {(finish_time - start_time).total_seconds()}')
