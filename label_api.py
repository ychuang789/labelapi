import uuid
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List, Dict

import uvicorn
from fastapi import FastAPI, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from celery_worker import label_data
from settings import CreateTaskRequestBody, SampleResultRequestBody, TaskListRequestBody, DatabaseInfo
from utils.database_core import scrap_data_to_df, get_create_task_query, get_count_query, get_tasks_query, \
    get_sample_query, create_state_table, insert2state, query_state
from utils.helper import get_logger
from utils.run_label_task import read_from_dir
from utils.selections import SampleResulTable


_logger = get_logger('label_API')

app = FastAPI(title="Labeling Task API")

@app.post('/api/tasks/', description='Create lableing task, '
                                     'edit the request body to fit your requirement. '
                                     'Make sure to save the information of tasks')
async def create(create_request_body: CreateTaskRequestBody):
    if create_request_body.start_time >= create_request_body.end_time:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=f'In setting.CreateTaskRequestBody start_time '
                                    f'must be earlier to end_time.')

    # create the tracking table `state` in `audience_result`
    engine = create_engine(DatabaseInfo.output_engine_info)
    _exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]
    if 'state' not in _exist_tables:
        create_state_table(_logger, schema=DatabaseInfo.output_schema)


    try:
        pattern = read_from_dir(create_request_body.model_type, create_request_body.predict_type)
    except Exception as e:
        _logger.error({"status_code":status.HTTP_400_BAD_REQUEST, "content":e})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=e)

    task_id = uuid.uuid1().hex
    setting: Dict = {"model_type": create_request_body.model_type,
                     "predict_type": create_request_body.predict_type,
                     "date_range": f"{create_request_body.start_time} - {create_request_body.end_time}",
                     "target_schema": create_request_body.target_schema,
                     "target_table": create_request_body.target_table,
                     "date_info": create_request_body.get_all,
                     "batch_size": create_request_body.batch_size
                     }
    date_info_dict = {"date_info_dict":
                          {'start_time': create_request_body.start_time,
                           'end_time': create_request_body.end_time}
                      }
    param = dict()
    param.update(setting)
    param.update({'pattern': pattern})
    param.update(date_info_dict)

    if create_request_body.predict_type == 'author_name':
        param['predict_type'] = "author"
    else:
        pass


    try:
        _logger.info('start the labeling worker ...')
        result = label_data.apply_async(args=(task_id, ),
                                        kwargs=param,
                                        task_id=task_id,
                                        expires=datetime.now() + timedelta(days=7))
        res = ""
        insert2state(task_id, result.state, setting.get('model_type'), setting.get('predict_type'),
                     setting.get('date_range'), setting.get('target_table'), datetime.now(),
                     res, _logger, schema=DatabaseInfo.output_schema)
    except Exception as e:
        _logger.error(f'cannot execute the task since {e}')
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=jsonable_encoder(e))


    _logger.info(f'API configuration: {setting}')


    config = {"task_id": task_id}
    config.update(param)

    return JSONResponse(status_code=status.HTTP_200_OK, content=config)

@app.get('/api/tasks/', description="Return a subset of task_id and task_status, "
                                    "you can pick a 'SUCCESS' task_id and get it's "
                                    "sample query information in /api/tasks/{task_id} api")
async def task_list():
    try:
        engine = create_engine(TaskListRequestBody.engine_info)
        query = get_tasks_query(TaskListRequestBody.table,
                                TaskListRequestBody.order_column,
                                TaskListRequestBody.number)
        result = engine.execute(query).fetchall()

        _dict = OrderedDict()
        col = ["task_id", "status", "model_type", "predict_type", "date_range", "target_table", "create_time", "result"]
        for i in result:
            temp = dict(zip(col, list(i)))
            _dict.update({
                temp.get("task_id"): {i: temp[i] for i in temp if i != 'task_id'}
            })

        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(_dict))
    except Exception as e:
        _logger.error(f"cannot connect to server since {e}")
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=jsonable_encoder(e))

@app.get('/api/tasks/{task_id}', description='input a task_id and output task_id with table_name for sampling query.')
async def check_status(task_id):
    try:
        engine = create_engine(DatabaseInfo.output_engine_info)
        _r = engine.execute(query_state(task_id)).fetchone()

        col = ["task_id", "status", "model_type", "predict_type", "date_range", "target_table", "create_time", "result"]

        _result = dict(zip(col, list(_r)))


        # _result = AsyncResult(task_id, app=label_data)
        # if _result.status == 'SUCCESS':

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

@app.get('/api/tasks/{task_id}/sample/', description='input a task_id and table_name to get the sampling result, you can input '
                                                     'task_id in /api/tasks/{task_id} to gain such information ')
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
        err_msg = f'invalid sql query, plz re-check it.'
        _logger.error({"status_code": status.HTTP_400_BAD_REQUEST, "content": f'{err_msg} Addition :{e}'})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{err_msg} Addition :{e}')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', debug=True)


