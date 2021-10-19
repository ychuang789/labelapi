import json
from datetime import datetime

from celery import Celery

from settings import CeleryConfig, DatabaseInfo
from utils.database_core import scrap_data_to_df, update2state
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
def label_data(task_id, schema, query, pattern, model_type, predict_type):
    _logger = get_logger('label_data')
    df = scrap_data_to_df(_logger, query, schema=schema)

    try:
        _output = labeling(task_id, df, model_type, predict_type, pattern, _logger, to_database=True)

        update2state(task_id, ','.join(_output) , _logger, schema=DatabaseInfo.output_schema)
    except:
        update2state(task_id, '', _logger, schema=DatabaseInfo.output_schema, seccess=False)
        raise RuntimeError('task failed !')

    return _output
