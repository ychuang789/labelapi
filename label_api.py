import uuid
from typing import List

import uvicorn
from celery.result import AsyncResult
from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from celery_worker import label_data
from settings import CreateTaskRequestBody, SampleResultRequestBody, TaskListRequestBody
from utils.database_core import scrap_data_to_df
from utils.helper import get_logger
from utils.run_label_task import read_from_dir


_logger = get_logger('label_API')

app = FastAPI(title="Labeling Task API",
              description="For helping AS department to labeling the data")

@app.post('/api/tasks/')
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
        pattern = read_from_dir(create_request_body.model_type.value, create_request_body.predict_type.value)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=e)

    if create_request_body.predict_type.value == 'author_name':

        query = f"SELECT * FROM {create_request_body.target_table} " \
                f"WHERE author IS NOT NULL " \
                f"AND post_time >= '{create_request_body.start_time}'" \
                f"AND post_time <= '{create_request_body.end_time}'"
    else:
        query = f"SELECT * FROM {create_request_body.target_table} " \
                f"WHERE {create_request_body.predict_type.value} IS NOT NULL " \
                f"AND post_time >= '{create_request_body.start_time}'" \
                f"AND post_time <= '{create_request_body.end_time}'"

    _logger.info('start the labeling worker ...')
    result = label_data.apply_async((task_id, create_request_body.target_schema,
                                     query, pattern, create_request_body.model_type.value,
                                     create_request_body.predict_type.value))

    setting.update({'task_id': f'{task_id};{result.id}'})
    _logger.info(f'API configuration: {setting}')

    return JSONResponse(status_code=status.HTTP_200_OK, content=setting)


@app.get('/api/tasks/')
async def task_list():
    try:
        engine = create_engine(TaskListRequestBody.sql_schema)
        count = engine.execute(f'SELECT COUNT(task_id) FROM celery_taskmeta').fetchall()[0][0]

        # if offset setting is greater than total rows of database, change it to half of count of database.
        offset = f'(SELECT COUNT(task_id)/2 FROM celery_taskmeta)' if TaskListRequestBody.offset > count \
            else TaskListRequestBody.offset

        query = f'SELECT task_id, status FROM {TaskListRequestBody.table} ' \
                f'WHERE id >= (SELECT id FROM {TaskListRequestBody.table} ' \
                f'ORDER BY {TaskListRequestBody.order_column} ' \
                f'LIMIT {offset}, 1) ' \
                f'LIMIT 10;'
        result = engine.execute(query).fetchall()

        _dict = {}
        for task_id, stat in result:
            _dict.update(
                {task_id: stat}
            )

        return JSONResponse(status_code=status.HTTP_200_OK, content=_dict)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=e)

@app.get('/api/tasks/<_id>', description='input a 69 digit of id which generate from create task api')
async def check_status(_id):
    try:
        _result = AsyncResult(_id.split(';')[1], app=label_data)
        return JSONResponse(status_code=status.HTTP_200_OK, content=_result.status)
    except Exception as e:
        err_msg = f'task id is not exist, plz re-check the task id.'
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=f'{err_msg} Addition :{e}')

@app.get('/api/tasks/<_id>/sample/', description='input a 69 digit of id which generate from create task api')
async def sample_result(_id: str):
    string = ''
    for i in range(len(SampleResultRequestBody.table)):
        string += f'{SampleResultRequestBody.table[i]} '

    query = f"SELECT * FROM {string}WHERE task_id = '{_id.split(';')[0]}' " \
            f"AND id >= (SELECT id FROM {string}ORDER BY {SampleResultRequestBody.order_column} " \
            f"LIMIT {SampleResultRequestBody.offset},1) " \
            f"LIMIT {SampleResultRequestBody.number}"

    try:
        result = scrap_data_to_df(_logger, query, schema=SampleResultRequestBody.sql_schema)

        return JSONResponse(status_code=status.HTTP_200_OK, content=result.to_json())
    except Exception as e:
        err_msg = f'invalid sql query, plz re-check it.'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{err_msg} Addition :{e}')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', debug=True)


