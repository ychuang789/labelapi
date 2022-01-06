import json
from dotenv import load_dotenv

from celery import Celery
from dump.groups.dump_core import DumpWorker

from utils.helper import get_logger, get_config
from workers.model_core import ModelingWorker
from workers.predict_core import PredictWorker


configuration = get_config()

celery_app = Celery(name=configuration.CELERY_NAME,
                    backend=configuration.CELERY_BACKEND,
                    broker=configuration.CELERY_BROKER)

celery_app.conf.update(enable_utc=configuration.CELERY_ENABLE_UTC)
celery_app.conf.update(timezone=configuration.CELERY_TIMEZONE)
celery_app.conf.update(result_extended=configuration.CELERY_RESULT_EXTENDED)
celery_app.conf.update(task_track_started=configuration.CELERY_TASK_TRACK_STARTED)
celery_app.conf.update(task_acks_late=configuration.CELERY_ACKS_LATE)
# celery_app.conf.update(task_serializer=configuration.CELERY_SERIALIZER)

@celery_app.task(name=f'{configuration.CELERY_NAME}.label_data', track_started=True)
# @memory_usage_tracking
def label_data(task_id: str, kwargs_json: str) -> None:
    kwargs = json.loads(kwargs_json)
    load_dotenv()
    labeling_worker = PredictWorker(task_id, kwargs.pop('MODEL_JOB_LIST'), **kwargs)
    labeling_worker.run_task()

@celery_app.task(name=f'{configuration.CELERY_NAME}.dump_result', track_started=True)
def dump_result(**kwargs):
    _logger = get_logger('dump')

    _logger.info('start dumping...')
    dump_workflow = DumpWorker(id_list=kwargs.get('ID_LIST'),
                               old_table_database=kwargs.get('OLD_TABLE_DATABASE'),
                               new_table_database=kwargs.get('NEW_TABLE_DATABASE'),
                               dump_database=kwargs.get('DUMP_DATABASE'))

    _logger.info(dump_workflow)

    try:
        _logger.info('start merging data')
        table_result = dump_workflow.run_merge()
        _logger.info(f'{table_result}')
    except Exception as e:
        _logger.error(f'failed to execute dumping flow, additional message {e}')
        raise e

    # _logger.info('dump to zip...')
    # dump_workflow.dump_zip()

@celery_app.task(name=f'{configuration.CELERY_NAME}.preparing', track_started=True)
def preparing(task_id, **kwargs):
    _logger = get_logger('modeling')
    _logger.info(f'start task {task_id}')
    model = ModelingWorker(model_name=kwargs['MODEL_TYPE'],
                           predict_type=kwargs['PREDICT_TYPE'],
                           dataset_number=kwargs['DATASET_NO'],
                           dataset_schema=kwargs['DATASET_DB'],
                           **kwargs['MODEL_INFO'])
    model.run_task(task_id=task_id, job_id=kwargs['MODEL_JOB_ID'])

@celery_app.task(name=f'{configuration.CELERY_NAME}.testing', track_started=True)
def testing(job_id, **kwargs):
    _logger = get_logger('modeling')
    _logger.info(f'start job {job_id}')
    model = ModelingWorker(model_name=kwargs['MODEL_TYPE'],
                           predict_type=kwargs['PREDICT_TYPE'],
                           dataset_number=kwargs['DATASET_NO'],
                           dataset_schema=kwargs['DATASET_DB'],
                           **kwargs['MODEL_INFO'])
    model.eval_outer_test_data(job_id)


# @celery_app.task(name=f'{configuration.CELERY_NAME}.testing', track_started=True)
# def testing(**kwargs):
#     kw = json.loads(kwargs)
#     return kwargs.get()
