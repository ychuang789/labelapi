from datetime import datetime
from typing import List, Dict

from celery import Celery
from sqlalchemy import create_engine

from settings import CeleryConfig, DatabaseInfo
from utils.database_core import update2state, get_data_by_batch
from utils.helper import get_logger
from utils.run_label_task import labeling
from utils.clean_up_result import run_workflow

name = CeleryConfig.name
celery_app = Celery(name=name,
                    backend=CeleryConfig.backend,
                    broker=CeleryConfig.broker)

celery_app.conf.update(enable_utc=CeleryConfig.enable_utc)
celery_app.conf.update(timezone=CeleryConfig.timezone)
celery_app.conf.update(result_extended=True)
celery_app.conf.update(task_track_started=True)


@celery_app.task(name=f'{name}.label_data', track_started=True)
def label_data(task_id, **kwargs):
    start_time = datetime.now()
    _logger = get_logger('label_data')

    try:
        engine = create_engine(DatabaseInfo.input_engine_info)
        count = engine.execute(f"SELECT COUNT(*) FROM {kwargs.get('target_table')} "
                               f"WHERE {kwargs.get('predict_type')} IS NOT NULL").fetchone()[0]
        _logger.info(f'length of table {kwargs.get("target_table")} is {count} rows')
    except Exception as e:
        err_msg = f"cannot connect to {kwargs.get('target_table')}, addition error message {e}"
        _logger.error(err_msg)
        raise ConnectionError(err_msg)

    table_set = set()
    for idx, element in enumerate(get_data_by_batch(count,
                                                    kwargs.get('predict_type'), kwargs.get('batch_size'),
                                                    kwargs.get('target_schema'), kwargs.get('target_table'),
                                                    date_info = kwargs.get('date_info'),
                                                    **kwargs.get('date_info_dict'))):

        _logger.info(f'Start calculating task {task_id} {kwargs.get("target_table")}_batch_{idx} ...')
        pred = "author_name" if kwargs.get('predict_type') == "author" else kwargs.get('predict_type')

        try:
            _output = labeling(task_id, element, kwargs.get('model_type'),
                               pred, kwargs.get('pattern'), _logger,
                               to_database=True)

            for i in _output:
                table_set.add(i)

            _logger.info(f'task {task_id} {kwargs.get("target_table")}_batch_{idx} finished labeling...')

        except Exception as e:
            update2state(task_id, '', _logger, schema=DatabaseInfo.output_schema, seccess=False)
            err_msg = f'task {task_id} failed at {kwargs.get("target_table")}_batch_{idx}, additional error message {e}'
            _logger.error(err_msg)
            raise err_msg

    update2state(task_id, ','.join(table_set), _logger, schema=DatabaseInfo.output_schema)

    try:
        result_dict = run_workflow(task_id, list(table_set), _logger, drop=False)
    except Exception as e:
        err_msg = f'task {task_id} failed at the cleaning stage, additional error message {e}'
        _logger.error(err_msg)
        raise err_msg


    finish_time = datetime.now()
    _logger.info(f'task {task_id} {kwargs.get("target_table")} done, total time is '
                 f'{(finish_time - start_time).total_seconds() / 60} minutes')

    return result_dict



