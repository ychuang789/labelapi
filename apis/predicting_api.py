import uuid

from fastapi import status, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import label_data, dump_result
from apis.input_class.predicting_input import TaskConfig, TaskSampleResult, AbortConfig, DumpConfig, DeleteConfig
from utils.database.database_helper import scrap_data_to_dict
from utils.general_helper import get_logger, uuid_validator
from workers.orm_core.predict_operation import PredictingCRUD

_logger = get_logger('label_API')

router = APIRouter(prefix='/tasks',
                   tags=['tasks'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )

@router.post('/', description='Create labeling task, edit the request body to fit your requirement. '
                              'Make sure to save the information of tasks, especially, `task_id`')
def create_task(body: TaskConfig):
    kwargs = body.__dict__
    if body.START_TIME >= body.END_TIME:
        err_info = {
            "error_code": 400,
            "error_message": "start_time must be earlier than end_time"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        # task_id = uuid.uuid1().hex
        label_data.apply_async(
            args=(
                body.TASK_ID, body.MODEL_ID_LIST, body.INPUT_SCHEMA,
                body.INPUT_TABLE, body.START_TIME, body.END_TIME,
                body.SITE_CONFIG,
            ),
            kwargs=kwargs,
            queue=body.QUEUE
        )

        err_info = {
            "error_code": 200,
            "error_message": body.TASK_ID
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

    orm_worker = PredictingCRUD()

    try:
        result = orm_worker.tasks_list()
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

@router.get('/{task_id}', description='Input a task_id and output status. If the task is success, '
                                      'return the result tables for querying sample results')
def check_status(task_id):

    if not uuid_validator(task_id):
        err_info = {
            "error_code": 400,
            "error_message": f"{task_id} is a improper task_id"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))

    orm_worker = PredictingCRUD()
    try:
        result = orm_worker.check_status(task_id)
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

    orm_worker = PredictingCRUD()

    try:
        query = orm_worker.sample_result(task_id)
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
def abort_task(body: AbortConfig):
    if not uuid_validator(body.TASK_ID):
        err_info = {
            "error_code": 400,
            "error_message": f"{body.TASK_ID} is a improper task_id"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))

    orm_worker = PredictingCRUD()
    try:
        orm_worker.abort_task(body.TASK_ID)
        err_info = {
            "error_code": 200,
            "error_message": f"successfully send break status to task {body.TASK_ID} in state"
        }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to send break status to task, additional error message: {e}"
        }
    finally:
        orm_worker.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.post('/delete/', description='delete the task')
def delete_task(body: DeleteConfig):
    if not uuid_validator(body.TASK_ID):
        err_info = {
            "error_code": 400,
            "error_message": f"{body.TASK_ID} is a improper task_id"
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))

    orm_worker = PredictingCRUD()

    try:
        orm_worker.delete_task(body.TASK_ID)
        err_info = {
            "error_code": 200,
            "error_message": f"successfully delete the task"
        }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to delete task, additional error message: {e}"
        }
    finally:
        orm_worker.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@router.post('/dump/', description='run dump workflow with task_id')
def dump_tasks(body: DumpConfig):
    try:
        dump_result.apply_async(
            args=(
                body.ID_LIST,
                body.OLD_TABLE_DATABASE,
                body.NEW_TABLE_DATABASE,
                body.DUMP_DATABASE
            ),
            queue=body.QUEUE
        )

        err_info = {
            "error_code": 200,
            "error_message": f"dump to {body.DUMP_DATABASE}"
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"dump flow is failed since of {e}"
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))
