import uuid

from fastapi import status, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import label_data, dump_result
from settings import TaskConfig, TaskSampleResult, AbortionConfig, DumpConfig
from utils.database.database_helper import scrap_data_to_dict
from utils.general_helper import get_logger, uuid_validator
from workers.orm_core.predict_orm_core import PredictORM

_logger = get_logger('label_API')

router = APIRouter(prefix='/tasks',
                   tags=['tasks'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )

@router.post('/', description='Create labeling task, edit the request body to fit your requirement. '
                                     'Make sure to save the information of tasks, especially, `task_id`')
def create_task(create_request_body: TaskConfig):
    config = create_request_body.__dict__

    if config.get('START_TIME') >= config.get('END_TIME'):
        err_info = {
            "error_code": 400,
            "error_message": "start_time must be earlier than end_time"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        task_id = uuid.uuid1().hex
        label_data.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))
        config.update({"task_id": task_id})

        err_info = {
            "error_code": 200,
            "error_message": task_id
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to start a labeling task, additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.get('/', description="Return a subset of task_id and task_info, "
                                    "you can pick a 'SUCCESS' task_id and get it's ")
def tasks_list():

    orm_worker = PredictORM()

    try:
        result = orm_worker.predict_tasks_list()
        err_info = {
            "error_code": 200,
            "error_message": "OK",
            "content": result
        }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": "cannot connect to state table",
            "content": e
        }
    finally:
        orm_worker.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.get('/{task_id}', description='Input a task_id and output status. If the task is successed, '
                                             'return the result tables for querying sample results')
def check_status(task_id):

    if not uuid_validator(task_id):
        err_info = {
            "error_code": 400,
            "error_message": f"{task_id} is a improper task_id"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))

    orm_worker = PredictORM()
    try:
        result = orm_worker.predict_check_status(task_id)
        err_info = {
            "error_code": 200,
            "error_message": result
        }
    except AttributeError as a:
        err_info = {
            "error_code": 404,
            "error_message": f"{task_id} is not found in the state table, additional error message: {a}"
        }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f'Addition error message:{e}',
        }
        _logger.error(f'{e}')
    finally:
        orm_worker.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.get('/{task_id}/sample/', description='Input a SUCCESS task_id and table_names to get the sampling result.'
                                                     'If you have no clue of task_id or table_names check the  '
                                                     '/api/tasks/{task_id} or /api/tasks/ before to gain such information ')
def sample_result(task_id: str):
    if not uuid_validator(task_id):
        err_info = {
            "error_code": 400,
            "error_message": f"{task_id} is a improper task_id"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))

    orm_worker = PredictORM()

    try:
        query = orm_worker.predict_sample_result(task_id)
        result = scrap_data_to_dict(query, TaskSampleResult.OUTPUT_SCHEMA)

        if len(result) == 0:
            err_info = {
                "error_code": 404,
                "error_message": "empty result, probably wrong combination of task_id and table_name, "
                                 "please check table state or use /api/tasks/{task_id} first"
            }
        else:
            err_info = {
                "error_code": 200,
                "error_message": result
            }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"Cannot scrape data from result tables. Additional error message: {e}"
        }
        _logger.error(err_info)

    finally:
        orm_worker.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.post('/abort/', description='aborting a task no matter it is executing')
def abort_task(abort_request_body: AbortionConfig):
    config = abort_request_body.__dict__
    task_id = config.get('TASK_ID', None)

    if not uuid_validator(task_id):
        err_info = {
            "error_code": 400,
            "error_message": f"{task_id} is a improper task_id"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))

    orm_worker = PredictORM()
    try:
        orm_worker.predict_abort_task(task_id)
        err_info = {
            "error_code": 200,
            "error_message" : f"successfully send break status to task {task_id} in state"
        }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to send break status to task, additional error message: {e}"
        }
    finally:
        orm_worker.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.post('/dump/', description='run dump workflow with task_id')
def dump_tasks(dump_request_body: DumpConfig):
    config = dump_request_body.__dict__

    try:
        dump_result.apply_async(kwargs=config, queue=config.get('QUEUE'))
        err_info = {
            "error_code": 200,
            "error_message": config
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"dump flow is failed since of {e}"
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))
