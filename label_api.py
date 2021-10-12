import uuid
from typing import List

import uvicorn
from celery.result import AsyncResult
from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse

from celery_worker import label_data
from settings import CreateTaskRequestBody, SampleResultRequestBody
from utils.database_core import scrap_data_to_df
from utils.helper import get_logger
from utils.run_label_task import read_from_dir


_logger = get_logger('label_API')

app = FastAPI(title="Labeling Task API",
              description="For helping AS department to labeling the data")

@app.post('/api/tasks/create_tasks/')
async def create(create_request_body: CreateTaskRequestBody):
    if create_request_body.start_time < create_request_body.end_time:
        pass
    else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=f'start time must be earlier to end time.')


    task_id = uuid.uuid1().hex
    setting = {"task_id": task_id,
               "model_type": create_request_body.model_type,
               "predict_type": create_request_body.predict_type,
               "date_range": f"{create_request_body.start_time} - {create_request_body.end_time}",
               "target_table": create_request_body.target_table}


    _logger.info('Preparing data...')
    try:
        pattern = read_from_dir(create_request_body.model_type.value, create_request_body.predict_type.value)
    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=f'rule file is not found.')

    if create_request_body.predict_type.value == 'author_name':

        query = f"SELECT * FROM {create_request_body.target_table} " \
                f"WHERE  author IS NOT NULL " \
                f"AND created_at >= '{create_request_body.start_time}'" \
                f"AND created_at <= '{create_request_body.end_time}'"
    else:
        query = f"SELECT * FROM {create_request_body.target_table} " \
                f"WHERE applied_feature='author' " \
                f"AND created_at >= '{create_request_body.start_time}'" \
                f"AND created_at <= '{create_request_body.end_time}'"

    _logger.info('start the labeling worker ...')
    result = label_data.apply_async((task_id, create_request_body.target_schema,
                                     query, pattern, create_request_body.model_type.value,
                                     create_request_body.predict_type.value))

    setting.update({'task_id': f'{task_id};{result.id}'})
    _logger.info(f'API configuration: {setting}')

    return JSONResponse(status_code=status.HTTP_200_OK, content=setting)


@app.get('/api/tasks/task_list/')
async def task_list(tasks: List[str] = Query(None)):
    try:
        status_dict = {}
        for i in range(len(tasks)):
            _result = AsyncResult(tasks[i].split(';')[1], app=label_data)
            temp = {
                tasks[i]: _result.status
            }
            status_dict.update(temp)

        return JSONResponse(status_code=status.HTTP_200_OK, content=status_dict)
    except:
        err_msg = f'invalid task list, plz retry.'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err_msg)

@app.get('/api/tasks/check_status/')
async def check_status(_id: str = Query(...)):
    try:
        _result = AsyncResult(_id.split(';')[1], app=label_data)
        return JSONResponse(status_code=status.HTTP_200_OK, content=_result.status)
    except:
        err_msg = f'task id is not exist, plz re-check the task id.'
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=err_msg)

@app.get('/api/tasks/sample/sample_result/')
async def sample_result(sample_request_body: SampleResultRequestBody, _id: str = Query(...)):
    string = ''
    for i in range(len(sample_request_body.table)):
        string += f'{sample_request_body.table[i]} '

    query = f"SELECT * FROM {string}WHERE task_id = '{_id.split(';')[0]}' " \
            f"AND id >= (SELECT id FROM {string}ORDER BY {sample_request_body.order_column} LIMIT {sample_request_body.offset},1) " \
            f"LIMIT {sample_request_body.number}"

    try:
        result = scrap_data_to_df(_logger, query, schema=sample_request_body.sql_schema)

        return JSONResponse(status_code=status.HTTP_200_OK, content=result.to_json())
    except:
        err_msg = f'invalid sql query, plz re-check it.'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err_msg)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', debug=True)


