import os
from dotenv import load_dotenv
from datetime import datetime
from itertools import chain

import pandas as pd
from celery import Celery
from settings import CeleryConfig, DatabaseInfo
from utils.database_core import update2state, get_data_by_batch, get_count
from utils.helper import get_logger
from utils.run_label_task import labeling
from utils.worker_core import memory_usage_tracking, track_cpu_usage

_logger = get_logger('label_data')

name = CeleryConfig.name
celery_app = Celery(name=name,
                    backend=CeleryConfig.backend,
                    broker=CeleryConfig.broker)

celery_app.conf.update(enable_utc=CeleryConfig.enable_utc)
celery_app.conf.update(timezone=CeleryConfig.timezone)
celery_app.conf.update(result_extended=True)
celery_app.conf.update(task_track_started=True)


@celery_app.task(name=f'{name}.label_data', track_started=True)
@memory_usage_tracking
def label_data(task_id, **kwargs):
    load_dotenv()
    start_time = datetime.now()
    cpu_info_df = pd.DataFrame(columns=['task_id', 'batch', 'cpu_percent', 'cpu_freq', 'cpu_load_avg'])

    # if kwargs.get('target_source'):
    #     target_source = list(chain(*kwargs.get('target_source').values()))
    #     if len(target_source) > 1:
    #         condition = tuple(target_source)
    #     else:
    #         condition = f'({target_source[0]})'
    # else:
    #     condition = kwargs.get('target_source')

    target_source_list = kwargs.get('target_source') if kwargs.get('target_source') != 'string' else None
    if target_source_list:
        if len(target_source_list) > 1:
            condition = tuple(target_source_list)
        else:
            condition = f'("{target_source_list[0]}")'
    else:
        condition = None


    try:
        engine_info = f"mysql+pymysql://{os.getenv('INPUT_USER')}:{os.getenv('INPUT_PASSWORD')}@" \
                      f"{os.getenv('INPUT_HOST')}:{os.getenv('INPUT_PORT')}/{kwargs.get('target_schema')}?charset=utf8mb4"
        count = get_count(engine_info, condition, **kwargs)
        if count == 0:
            _logger.info(f'length of table {kwargs.get("target_table")} is {count} rows')
            return f'length of table {kwargs.get("target_table")} is {count} rows, skip the task {task_id}'
        else:
            pass
        _logger.info(f'length of table {kwargs.get("target_table")} is {count} rows')

    except Exception as e:
        err_msg = f"cannot connect to {kwargs.get('target_table')}, addition error message {e}"
        _logger.error(err_msg)
        raise ConnectionError(err_msg)

    # if count > 2000000:
    #     batch_size = 1000000
    # else:
    #     batch_size = count // 2

    batch_size = 10000

    table_set = set()
    row_number = 0
    for idx, element in enumerate(get_data_by_batch(count,
                                                    kwargs.get('predict_type'), batch_size,
                                                    kwargs.get('target_schema'), kwargs.get('target_table'),
                                                    condition,
                                                    date_info = kwargs.get('date_info'),
                                                    chunk_by_source = kwargs.get('chunk_by_source'),
                                                    **kwargs.get('date_info_dict'))):

        _logger.info(f'Start calculating task {task_id} {kwargs.get("target_table")}_batch_{idx} ...')
        pred = "author_name" if kwargs.get('predict_type') == "author" else kwargs.get('predict_type')

        try:
            _output, row_num = labeling(task_id, element, kwargs.get('model_type'),
                               pred, kwargs.get('pattern'), _logger)

            row_number += row_num
            for i in _output:
                table_set.add(i)

            _logger.info(f'task {task_id} {kwargs.get("target_table")}_batch_{idx} finished labeling...')

            cpu_track = track_cpu_usage()
            cpu_track.update({'task_id': task_id, 'batch': idx})
            cpu_info_df = cpu_info_df.append(cpu_track, ignore_index=True)

        except Exception as e:
            update2state(task_id, '', _logger, schema=DatabaseInfo.output_schema, success=False)
            err_msg = f'task {task_id} failed at {kwargs.get("target_table")}_batch_{idx}, additional error message {e}'
            _logger.error(err_msg)
            raise err_msg


    update2state(task_id, ','.join(table_set), _logger, count, row_number, schema=DatabaseInfo.output_schema)


    finish_time = datetime.now()
    _logger.info(f'task {task_id} {kwargs.get("target_table")} done, total time is '
                 f'{(finish_time - start_time).total_seconds() / 60} minutes')

    cpu_info_df.to_csv(f'save_file/{task_id}_cpu_info.csv', encoding='utf-8-sig', index=False)

    return {task_id: table_set}

# @celery_app.task(name=f'{name}.testing', track_started=True)
# @memory_usage_tracking
# def testing():
#     a, b = 0, 1
#     for i in range(10000):
#         temp = b
#         b += a
#         a = temp
#
#     return b

