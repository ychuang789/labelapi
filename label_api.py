import uuid
from collections import OrderedDict
from typing import List

import uvicorn
from celery.result import AsyncResult
from fastapi import FastAPI, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from celery_worker import label_data
from settings import CreateTaskRequestBody, SampleResultRequestBody, TaskListRequestBody
from utils.database_core import scrap_data_to_df, get_create_task_query, get_count_query, get_tasks_query, \
    get_sample_query
from utils.helper import get_logger
from utils.run_label_task import read_from_dir
from utils.selections import SampleResulTable


_logger = get_logger('label_API')

app = FastAPI(title="Labeling Task API",
              description="For helping AS department to labeling the data.")

@app.post('/api/tasks/', description='Create lableing task, '
                                     'edit the request body to fit your requirement. '
                                     'Make sure to save the information of tasks')
async def create(create_request_body: CreateTaskRequestBody):
    if create_request_body.start_time >= create_request_body.end_time:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=f'In setting.CreateTaskRequestBody start_time '
                                    f'must be earlier to end_time.')

    task_id = uuid.uuid1().hex
    setting = {"task_id": task_id,
               "model_type": create_request_body.model_type,
               "predict_type": create_request_body.predict_type,
               "date_range": f"{create_request_body.start_time} - {create_request_body.end_time}",
               "target_table": create_request_body.target_table}

    _logger.info('Preparing data...')
    try:
        pattern = read_from_dir(create_request_body.model_type, create_request_body.predict_type)
    except Exception as e:
        _logger.error({"status_code":status.HTTP_400_BAD_REQUEST, "content":e})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=e)

    if create_request_body.predict_type == 'author_name':
        pred_type = "author"
        query = get_create_task_query(create_request_body.target_table,
                                      pred_type,
                                      create_request_body.start_time,
                                      create_request_body.end_time)
    else:

        query = get_create_task_query(create_request_body.target_table,
                                      create_request_body.predict_type,
                                      create_request_body.start_time,
                                      create_request_body.end_time)

    _logger.info('start the labeling worker ...')
    result = label_data.apply_async((task_id, create_request_body.target_schema,
                                     query, pattern, create_request_body.model_type,
                                     create_request_body.predict_type))

    setting.update({'celery_id': f'{result.id}'})
    _logger.info(f'API configuration: {setting}')

    return JSONResponse(status_code=status.HTTP_200_OK, content=setting)

@app.get('/api/tasks/', description="Return a subset of celery_id and celery_status, "
                                    "you can pick a 'SUCCESS' celery_id and get it's "
                                    "sample query information in /api/tasks/{celery_id} api")
async def task_list():
    try:
        engine = create_engine(TaskListRequestBody.sql_schema)
        count = engine.execute(get_count_query()).fetchall()[0][0]

        # if offset setting is greater than total rows of database, change it to half of count of database.
        # offset = f'(SELECT COUNT(task_id)/2 FROM celery_taskmeta)' if TaskListRequestBody.offset > count \
        #     else TaskListRequestBody.offset

        query = get_tasks_query(TaskListRequestBody.table,
                                TaskListRequestBody.order_column,
                                # offset,
                                TaskListRequestBody.number)
        result = engine.execute(query).fetchall()

        _dict = OrderedDict()
        for task_id, stat in result:
            _dict.update(
                {task_id: stat}
            )

        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(_dict))
    except Exception as e:
        _logger.error({"status_code":status.HTTP_500_INTERNAL_SERVER_ERROR, "content":e})
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(e))

@app.get('/api/tasks/{celery_id}', description='input a celery_id and output task_id with table_name for sampling query.')
async def check_status(celery_id):
    try:
        _result = AsyncResult(celery_id, app=label_data)
        if _result.status == 'SUCCESS':
            result_content = {
                _result.status: _result.get()
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=result_content)
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content=_result.status)

    except Exception as e:
        err_msg = f'task id is not exist, plz re-check the task id.'
        _logger.error({"status_code": status.HTTP_404_NOT_FOUND, "content": f'{err_msg} Addition :{e}'})
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=f'{err_msg} Addition :{e}')

@app.get('/api/tasks/{task_id}/sample/', description='input a task_id and table_name to get the sampling result, you can input '
                                                     'celery_id in /api/tasks/{celery_id} to gain such information ')
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
                                 SampleResultRequestBody.order_column,
                                 SampleResultRequestBody.offset,
                                 SampleResultRequestBody.number)
        q += query
        if i != len(table_name)-1:
            q += ' UNION ALL '
        else:
            pass

    try:
        result = scrap_data_to_df(_logger, q, schema=SampleResultRequestBody.sql_schema, _to_dict=True)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        err_msg = f'invalid sql query, plz re-check it.'
        _logger.error({"status_code": status.HTTP_400_BAD_REQUEST, "content": f'{err_msg} Addition :{e}'})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{err_msg} Addition :{e}')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', debug=True)


