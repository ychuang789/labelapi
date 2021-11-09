import uuid
from collections import OrderedDict
from datetime import datetime
from typing import List, Dict

import uvicorn
from fastapi import FastAPI, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from celery import chain
from celery_worker import label_data, generate_production
from settings import APIConfig, CreateTaskRequestBody, SampleResultRequestBody, TaskListRequestBody, DatabaseInfo
from utils.database_core import scrap_data_to_dict, get_tasks_query_recent, \
    get_sample_query, create_state_table, insert2state, query_state_by_id
from utils.helper import get_logger
from utils.run_label_task import read_from_dir
from utils.selections import SampleResulTable



_logger = get_logger('label_API')

app = FastAPI(title=APIConfig.title, description=APIConfig.description, version=APIConfig.version)

@app.post('/api/tasks/', description='Create lableing task, '
                                     'edit the request body to fit your requirement. '
                                     'Make sure to save the information of tasks, especially, `task_id`')
async def create_task(create_request_body: CreateTaskRequestBody):
    config = create_request_body.__dict__

    if config.get('start_time') >= config.get('end_time'):
        err_info = {
            "error_code": 400,
            "error_message": "start_time must be earlier than end_time"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        engine = create_engine(DatabaseInfo.output_engine_info).connect()
        _exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]
        if 'state' not in _exist_tables:
            create_state_table(_logger, schema=DatabaseInfo.output_schema)
        engine.close()
    except Exception as e:
        err_info = {
            "error_code": 503,
            "error_message": f"Cannot connect to output schema, additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        pattern = read_from_dir(config.get('model_type'), config.get('predict_type'))
        config.update(
            {'pattern': pattern}
        )
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"Cannot read pattern file, probably unknown file path or file is not exist"
                             f", additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    # since the source database author column name is `author`
    if config.get('predict_type') == 'author_name':
        config['predict_type'] = "author"
    else:
        pass

    _logger.info('start labeling task flow ...')
    try:
        task_id = uuid.uuid1().hex

        result = chain(
            label_data.signature(
                args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('queue')
            )
            | generate_production.signature(
                args=(task_id,), kwargs=config, countdown=config.get('countdown'), queue=config.get('queue')

            )
        )()

        config.update({"date_range": f"{config.get('start_time')} - {config.get('end_time')}"})

        insert2state(task_id, result.state, config.get('model_type'), config.get('predict_type'),
                     config.get('date_range'), config.get('target_schema'), datetime.now(), "",
                     _logger, schema=DatabaseInfo.output_schema)

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to start a labeling task, additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    config.update({"task_id": task_id})
    config.pop('pattern')

    err_info = {
        "error_code": 200,
        "error_message": config
    }

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/api/tasks/', description="Return a subset of task_id and task_info, "
                                    "you can pick a 'SUCCESS' task_id and get it's ")
async def tasks_list():
    try:
        result = get_tasks_query_recent(TaskListRequestBody.order_column,
                                       TaskListRequestBody.number)
        err_info = {
            "error_code": 200,
            "error_message": "OK",
            "content": result
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:

        err_info = {
            "error_code": 500,
            "error_message": "Cannot connect to state table",
            "content": e
        }
        _logger.error(f"{e}")
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/api/tasks/{task_id}', description='Input a task_id and output status. If the task is successed, '
                                             'return the result tables for querying sample results')
async def check_status(task_id):
    try:
        result = query_state_by_id(task_id)
        err_info = {
            "error_code": 200,
            "error_message": "OK",
            "status": result.get('stat'),
            "result": result.get('result')
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:
        err_info = {
            "error_code": 400,
            "error_message": f'task id is not exist, plz re-check the task id. Addition error message:{e}',
            "status": None,
            "result": None
        }
        _logger.error(f'{e}')
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/api/tasks/{task_id}/sample/', description='Input a SUCCESS task_id and table_names to get the sampling result.'
                                                     'If you have no clue of task_id or table_names check the  '
                                                     '/api/tasks/{task_id} or /api/tasks/ before to gain such information ')
async def sample_result(task_id: str,
                        table_name: List[SampleResulTable] = Query(..., description='press Ctrl/Command with '
                                                                                    'right key of mouse to '
                                                                                    'choose multiple tables')):
    if len(task_id) != 32:
        err_info = {
            "error_code": 400,
            "error_message": f'{task_id} is not in proper format, expect 32 digits get {len(task_id)} digits.'
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    q = ''
    for i in range(len(table_name)):
        query = get_sample_query(task_id,table_name[i],
                                 SampleResultRequestBody.number)
        q += query
        if i != len(table_name)-1:
            q += ' UNION ALL '
        else:
            pass

    try:
        result = scrap_data_to_dict(q, SampleResultRequestBody.schema_name)

        if len(result) == 0:
            err_info = {
                "error_code": 400,
                "error_message": "empty result, probably wrong combination of task_id and table_name"
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))
        else:
            err_info = {
                "error_code": 200,
                "error_message": result
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"Cannot scrape data from result tables. Additional error message {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_info))


if __name__ == '__main__':
    uvicorn.run(app, host=APIConfig.host, debug=True)


