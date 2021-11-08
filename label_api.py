import uuid
from collections import OrderedDict
from datetime import datetime
from typing import List

import uvicorn
from fastapi import FastAPI, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from celery import chain
from celery_worker import label_data, generate_production
from settings import CreateTaskRequestBody, SampleResultRequestBody, \
    TaskListRequestBody, DatabaseInfo
from utils.database_core import scrap_data_to_df, get_tasks_query, \
    get_sample_query, create_state_table, insert2state, query_state
from utils.helper import get_logger
from utils.run_label_task import read_from_dir
from utils.selections import SampleResulTable


_logger = get_logger('label_API')

description = """
This service is created by department of Research and Development 2 to help Audience labeling.    
#### Item   
1. create_task : a post api which create a labeling task via the information in the request body.   
2. task_list : return the recent tasks and tasks information.    
3. check_status : return a single task status and results if success via task_id.  
4. sample_result : return the labeling results from database via task_id and table information.    
#### Users  
For eland staff only. 
"""

app = FastAPI(title="Audience API",
              description=description,
              version='2.0'
              )

@app.post('/api/tasks/', description='Create lableing task, '
                                     'edit the request body to fit your requirement. '
                                     'Make sure to save the information of tasks, especially, `task_id`')
async def create_task(create_request_body: CreateTaskRequestBody):
    config = create_request_body.__dict__

    # check the datetime request body
    if config.get('start_time') >= config.get('end_time'):
        err_info = {
            "error_code": 400,
            "error_message": "start_time must be earlier than end_time"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    # create the tracking table `state` in `audience_result`
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

    # read the pattern
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

    # change `author_name` to `author` to fit database column name
    if config.get('predict_type') == 'author_name':
        config['predict_type'] = "author"
    else:
        pass

    # run task
    _logger.info('start labeling task flow ...')
    try:
        task_id = uuid.uuid1().hex

        result = chain(
            label_data.signature(
                args=(task_id,), kwargs=config, task_id=task_id
            )
            | generate_production.signature(
                args=(task_id,), kwargs=config, countdown=config.get('countdown')

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
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@app.get('/api/tasks/', description="Return a subset of task_id and task_info, "
                                    "you can pick a 'SUCCESS' task_id and get it's ")
async def tasks_list():
    try:
        engine = create_engine(TaskListRequestBody.engine_info)
        query = get_tasks_query(TaskListRequestBody.table,
                                TaskListRequestBody.order_column,
                                TaskListRequestBody.number)
        result = engine.execute(query).fetchall()

        _dict = OrderedDict()
        col = ["task_id", "status", "model_type", "predict_type", "date_range", "target_table", "create_time",
               "peak_memory", "length_receive_table", "length_output_table", "result", "rate_of_label"]
        for i in result:
            temp = dict(zip(col, list(i)))
            _dict.update({
                temp.get("task_id"): {i: temp[i] for i in temp if i != 'task_id'}
            })

        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(_dict))
    except Exception as e:
        _logger.error(f"cannot connect to server since {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(e))

@app.get('/api/tasks/{task_id}', description='Input a task_id and output status. If the task is successed, '
                                             'return the result tables for querying sample results')
async def check_status(task_id):
    try:
        engine = create_engine(DatabaseInfo.output_engine_info)
        _r = engine.execute(query_state(task_id)).fetchone()

        col = ["task_id", "status", "model_type", "predict_type", "date_range", "target_table", "create_time",
               "peak_memory", "length_receive_table", "length_output_table", "result", "rate_of_label"]

        _result = dict(zip(col, list(_r)))


        if _result.get('status') == 'SUCCESS':
            result_content = {
                _result.get('status'): _result.get('result')
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=result_content)
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content=_result.get('status'))

    except Exception as e:
        err_msg = f'task id is not exist, plz re-check the task id.'
        _logger.error({"status_code": status.HTTP_404_NOT_FOUND, "content": f'{err_msg} Addition :{e}'})
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=e)

@app.get('/api/tasks/{task_id}/sample/', description='Input a SUCCESS task_id and table_names to get the sampling result.'
                                                     'If you have no clue of task_id or table_names check the  '
                                                     '/api/tasks/{task_id} or /api/tasks/ before to gain such information ')
async def sample_result(task_id: str,
                        table_name: List[SampleResulTable] = Query(..., description='press Ctrl/Command with '
                                                                                    'right key of mouse to '
                                                                                    'choose multiple tables')):
    if len(task_id) != 32:
        err_msg = f'{task_id} is not in proper format, expect 32 digits get {len(task_id)} digits.'
        _logger.error({"status_code": status.HTTP_400_BAD_REQUEST, "content": f'{err_msg}'})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{err_msg}')

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
        result = scrap_data_to_df(_logger, q, schema=SampleResultRequestBody.schema_name, _to_dict=True)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        err_msg = f'invalid query, plz re-check it.'
        _logger.error({"status_code": status.HTTP_400_BAD_REQUEST, "content": f'{err_msg} Addition :{e}'})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{err_msg} Addition :{e}')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', debug=True)


