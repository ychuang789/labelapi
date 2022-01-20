from celery import Celery
from dump.groups.dump_core import DumpWorker

from utils.general_helper import get_logger, get_config
from workers.modeling.model_core import ModelingWorker
from workers.predicting.predict_core import PredictWorker


configuration = get_config()

celery_app = Celery(name=configuration.CELERY_NAME,
                    backend=configuration.CELERY_BACKEND,
                    broker=configuration.CELERY_BROKER)

celery_app.conf.update(enable_utc=configuration.CELERY_ENABLE_UTC)
celery_app.conf.update(timezone=configuration.CELERY_TIMEZONE)
celery_app.conf.update(result_extended=configuration.CELERY_RESULT_EXTENDED)
celery_app.conf.update(task_track_started=configuration.CELERY_TASK_TRACK_STARTED)
celery_app.conf.update(task_acks_late=configuration.CELERY_ACKS_LATE)

@celery_app.task(name=f'{configuration.CELERY_NAME}.label_data', ignore_result=True)
def label_data(task_id, model_job_list, input_schema, input_table, start_time, end_time,
               site_config, **kwargs) -> None:

    labeling_worker = PredictWorker(task_id=task_id, model_job_list=model_job_list,
                                    input_schema=input_schema, input_table=input_table,
                                    start_time=start_time, end_time=end_time,
                                    site_connection_info=site_config, **kwargs)
    try:
        labeling_worker.add_task_info()
        labeling_worker.run_task()
    except Exception as e:
        labeling_worker.orm_cls.session.rollback()
        raise e
    finally:
        labeling_worker._dispose()

@celery_app.task(name=f'{configuration.CELERY_NAME}.dump_result', ignore_result=True)
def dump_result(id_list, old_table_database, new_table_database, dump_database):
    _logger = get_logger('dump')

    _logger.info('start dumping...')
    dump_workflow = DumpWorker(id_list=id_list,
                               old_table_database=old_table_database,
                               new_table_database=new_table_database,
                               dump_database=dump_database)

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

@celery_app.task(name=f'{configuration.CELERY_NAME}.preparing', ignore_result=True)
def modeling_task(task_id, model_name, predict_type, dataset_number, dataset_schema, **kwargs):
    _logger = get_logger('modeling')
    _logger.info(f'start task {task_id}')
    model = ModelingWorker(model_name=model_name,
                           predict_type=predict_type,
                           dataset_number=dataset_number,
                           dataset_schema=dataset_schema,
                           **kwargs)
    model.run_task(task_id=task_id, job_id=kwargs['MODEL_JOB_ID'])

@celery_app.task(name=f'{configuration.CELERY_NAME}.testing', ignore_result=True)
def testing(job_id, model_name, predict_type, dataset_number, dataset_schema, **kwargs):
    _logger = get_logger('modeling')
    _logger.info(f'start job {job_id}')
    model = ModelingWorker(model_name=model_name,
                           predict_type=predict_type,
                           dataset_number=dataset_number,
                           dataset_schema=dataset_schema,
                           **kwargs)
    model.eval_outer_test_data(job_id)


# @celery_app.task(name=f'{configuration.CELERY_NAME}.testing', track_started=True)
# def testing(**kwargs):
#     kw = json.loads(kwargs)
#     return kwargs.get()
