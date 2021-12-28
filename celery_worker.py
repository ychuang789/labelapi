import json
from typing import Dict, Optional


from dotenv import load_dotenv
from datetime import datetime

from celery import Celery

from dump.dump_production import DumpFlow
from settings import DatabaseConfig
from utils.database_core import update2state, get_batch_by_timedelta, check_break_status, update2state_nodata, \
    update2state_temp_result_table
from utils.helper import get_logger, get_config
from utils.model_core import ModelingWorker
from utils.run_label_task import labeling
from utils.task_generate_production_core import TaskGenerateOutput
from utils.task_info_core import TaskInfo

configuration = get_config()

celery_app = Celery(name=configuration.CELERY_NAME,
                    backend=configuration.CELERY_BACKEND,
                    broker=configuration.CELERY_BROKER)

celery_app.conf.update(enable_utc=configuration.CELERY_ENABLE_UTC)
celery_app.conf.update(timezone=configuration.CELERY_TIMEZONE)
celery_app.conf.update(result_extended=configuration.CELERY_RESULT_EXTENDED)
celery_app.conf.update(task_track_started=configuration.CELERY_TASK_TRACK_STARTED)
celery_app.conf.update(task_acks_late=configuration.CELERY_ACKS_LATE)
celery_app.conf.update(task_serializer=configuration.CELERY_SERIALIZER)

@celery_app.task(name=f'{configuration.CELERY_NAME}.label_data', track_started=True)
# @memory_usage_tracking
def label_data(task_id: str, kwargs_json: str) -> Optional[str]:
    kwargs = json.loads(kwargs_json)
    _logger = get_logger('label_data')

    if check_break_status(task_id) == 'BREAK':
        _logger.info(f"task {task_id} is abort by the external user")
        return None

    load_dotenv()
    start_time = datetime.now()
    # cpu_info_df = pd.DataFrame(columns=['task_id', 'batch', 'cpu_percent', 'cpu_freq', 'cpu_load_avg'])

    start_date = kwargs.get('START_TIME')
    end_date = kwargs.get('END_TIME')
    start_date_d = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
    end_date_d = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S")
    site_connection_info: Dict = kwargs.get('SITE_CONFIG') if kwargs.get('SITE_CONFIG') else None

    table_dict: Dict = {}
    count = 0
    row_number = 0

    for idx, elements in enumerate(get_batch_by_timedelta(kwargs.get('INPUT_SCHEMA'),
                                                          kwargs.get('PREDICT_TYPE'),
                                                          kwargs.get('INPUT_TABLE'),
                                                          start_date_d,
                                                          end_date_d,
                                                          site_input=site_connection_info)):

        _logger.info(f'Start calculating task {task_id} {kwargs.get("INPUT_SCHEMA")}.'
                     f'{kwargs.get("INPUT_TABLE")}_batch_{idx} ...')

        element, date_checkpoint = elements

        if isinstance(element, str):
            update2state(task_id, '', _logger,
                         schema=DatabaseConfig.OUTPUT_SCHEMA,
                         success=False,
                         check_point=date_checkpoint,
                         error_message=elements)
            return None


        if check_break_status(task_id) == 'BREAK':
            _logger.info(f"task {task_id} is abort by the external user in checkpoint {date_checkpoint}")
            return None

        # change the `author` back to `author_name` to fit the label modeling
        pred = "author_name" if kwargs.get('PREDICT_TYPE') == "author" else kwargs.get('PREDICT_TYPE')

        if element.empty:
            continue

        count += len(element)

        try:
            _output, row_num = labeling(task_id, element, kwargs.get('MODEL_TYPE'),
                               pred, kwargs.get('PATTERN'), _logger)

            row_number += row_num

            for k,v in _output.items():
                if table_dict.get(k):
                    table_dict[k] = table_dict.get(k).union(v)
                else:
                    table_dict.update({k:v})


            if table_dict:
                update2state_temp_result_table(task_id,
                                               DatabaseConfig.OUTPUT_SCHEMA,
                                               ','.join(table_dict.keys()),
                                               _logger)

            _logger.info(f'task {task_id} {kwargs.get("INPUT_SCHEMA")}.'
                         f'{kwargs.get("INPUT_TABLE")}_batch_{idx} finished labeling...')

        except Exception as e:
            update2state(task_id, '', _logger,
                         schema=DatabaseConfig.OUTPUT_SCHEMA,
                         success=False,
                         check_point=date_checkpoint,
                         error_message=e)

            err_msg = f'task {task_id} failed at {kwargs.get("INPUT_SCHEMA")}.' \
                      f'{kwargs.get("INPUT_TABLE")}_batch_{idx}, additional error message {e}'
            _logger.error(err_msg)
            raise e

    finish_time = (datetime.now() - start_time).total_seconds() / 60
    _logger.info(f'task {task_id} {kwargs.get("INPUT_SCHEMA")}.'
                 f'{kwargs.get("INPUT_TABLE")} done, total time is '
                 f'{finish_time} minutes')

    update2state(task_id, ','.join(table_dict.keys()), _logger, count, row_number, finish_time,
                 schema=DatabaseConfig.OUTPUT_SCHEMA,
                 uniq_source_author=','.join([str(len(i)) for i in table_dict.values()]))

    # return json.dumps(list(table_dict.keys()), ensure_ascii=False)

    output_table =  list(table_dict.keys())
    start_time = datetime.now()

    if check_break_status(task_id) == 'BREAK':
        _logger.info(f"task {task_id} is abort by the external user, also skip generating production")
        return None

    if len(output_table) == 0:
        update2state_nodata(task_id, DatabaseConfig.OUTPUT_SCHEMA, _logger)
        return

    for tb in output_table:
        _logger.info(f'start generating output for table {tb}...')

        generate_production = TaskGenerateOutput(task_id,
                                                 kwargs.get('OUTPUT_SCHEMA'),
                                                 tb, _logger)
        _output_table_name, row_num = generate_production.clean()

        _logger.info(f'finish generating output for table {tb}')
        _logger.info(f'start generating task validation for table {tb} ...')

        task_info_obj = TaskInfo(task_id,
                                 kwargs.get('OUTPUT_SCHEMA'),
                                 tb,
                                 kwargs.get('INPUT_TABLE'),
                                 row_num, _logger)

        _logger.info(f'start calculating rate_of_label for table {tb}...')
        task_info_obj.generate_output()
        _logger.info(f'finish calculating rate_of_label for table {tb}')

        _logger.info(
            f'total time for {task_id}: {tb} is '
            f'{(datetime.now() - start_time).total_seconds() / 60} minutes')

    _logger.info(f'finish task {task_id} generate_production, total time: '
                 f'{(datetime.now() - start_time).total_seconds() / 60} minutes')


@celery_app.task(name=f'{configuration.CELERY_NAME}.dump_result', track_started=True)
def dump_result(**kwargs):
    _logger = get_logger('dump')

    _logger.info('start dumping...')
    dump_workflow = DumpFlow().generate_dump_flow(kwargs.get('group'), kwargs.get('task_ids'), kwargs.get('previous'))

    if dump_workflow:
        _logger.info('dump group is not found...plz re-check it')
        return None

    try:
        _logger.info('start merging data')
        dump_workflow.run_merge()

    except Exception as e:
        _logger.error(f'failed to execute dumping flow, additional message {e}')
        raise e

    _logger.info('dump to zip...')
    dump_workflow.dump_zip()


@celery_app.task(name=f'{configuration.CELERY_NAME}.modeling', track_started=True)
def modeling(task_id, **kwargs):
    _logger = get_logger('modeling')
    _logger.info(f'start task {task_id}')
    model = ModelingWorker(model_name=kwargs['MODEL_TYPE'],
                           predict_type=kwargs['PREDICT_TYPE'],
                           dataset_number=kwargs['DATASET_NO'],
                           dataset_schema=kwargs['DATASET_DB'],
                           **kwargs['MODEL_INFO'])
    model.run_task(task_id)


# @celery_app.task(name=f'{configuration.CELERY_NAME}.testing', track_started=True)
# def testing(**kwargs):
#     kw = json.loads(kwargs)
#     return kwargs.get()
