import json
import uuid
from datetime import datetime

import uvicorn
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import create_engine

from celery_worker import label_data, dump_result
from settings import DatabaseConfig, TaskConfig, TaskList, TaskSampleResult, AbortionConfig, DumpConfig
from utils.database_core import scrap_data_to_dict, get_tasks_query_recent, \
    get_sample_query, create_state_table, insert2state, query_state_by_id, get_table_info, send_break_signal_to_state
from utils.helper import get_logger, get_config

configuration = get_config()

_logger = get_logger('label_API')

description = """
This service is created by department of Research and Development 2 to help Audience labeling.    

#### Item    

1. create_task : a post api which create a labeling task via the information in the request body.    
2. task_list : return the recent tasks and tasks information.     
3. check_status : return a single task status and results if success via task_id.   
4. sample_result : return the labeling results from database via task_id and table information.    
5. abort_task : break the task.   
6. dump_tasks : dump tasks to ZIP.   

#### Users   
For eland staff only.  
"""

app = FastAPI(title=configuration.API_TITLE, description=description, version=configuration.API_VERSION)

@app.post('/api/tasks/', description='Create labeling task, '
                                     'edit the request body to fit your requirement. '
                                     'Make sure to save the information of tasks, especially, `task_id`')
async def create_task(create_request_body: TaskConfig):
    config = create_request_body.__dict__

    if config.get('START_TIME') >= config.get('END_TIME'):
        err_info = {
            "error_code": 400,
            "error_message": "start_time must be earlier than end_time"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        engine = create_engine(DatabaseConfig.OUTPUT_ENGINE_INFO).connect()
        _exist_tables = [i[0] for i in engine.execute('SHOW TABLES').fetchall()]
        if 'state' not in _exist_tables:
            create_state_table(_logger, schema=DatabaseConfig.OUTPUT_SCHEMA)
        engine.close()
    except Exception as e:
        err_info = {
            "error_code": 503,
            "error_message": f"cannot connect to output schema, additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    if config.get('PREDICT_TYPE') == 'author_name':
        config['PREDICT_TYPE'] = "author"
    else:
        pass

    _logger.info('start labeling task flow ...')
    try:
        task_id = uuid.uuid1().hex
        # _config = json.dumps(config, ensure_ascii=False)
        # result = label_data.apply_async(args=(task_id, _config), task_id=task_id, queue=config.get('QUEUE'))
        result = label_data.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))

        # result = chain(
        #     label_data.signature(
        #         args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE')
        #     )
        #     | generate_production.signature(
        #         args=(task_id,), kwargs=config, countdown=config.get('COUNTDOWN'), queue=config.get('QUEUE')
        #
        #     )
        # )()

        config.update({"date_range": f"{config.get('START_TIME')} - {config.get('END_TIME')}"})

        insert2state(task_id, result.state, config.get('MODEL_TYPE'), config.get('PREDICT_TYPE'),
                     config.get('date_range'), config.get('INPUT_SCHEMA'), datetime.now(), "",
                     _logger, schema=DatabaseConfig.OUTPUT_SCHEMA)

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to start a labeling task, additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    config.update({"task_id": task_id})

    err_info = {
        "error_code": 200,
        "error_message": config
    }

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/api/tasks/', description="Return a subset of task_id and task_info, "
                                    "you can pick a 'SUCCESS' task_id and get it's ")
async def tasks_list():
    try:
        result = get_tasks_query_recent(TaskList.ORDER_COLUMN,
                                       TaskList.NUMBER)
        err_info = {
            "error_code": 200,
            "error_message": "OK",
            "content": result
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:

        err_info = {
            "error_code": 500,
            "error_message": "cannot connect to state table",
            "content": e
        }
        _logger.error(f"{e}")
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/api/tasks/{task_id}', description='Input a task_id and output status. If the task is successed, '
                                             'return the result tables for querying sample results')
async def check_status(task_id):
    try:
        result = query_state_by_id(task_id)
        if result:
            err_info = {
                "error_code": 200,
                "error_message": result
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))
        else:
            err_info = {
                "error_code": 404,
                "error_message": f"{task_id} status is not found, plz re-check the task_id"
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f'Addition error message:{e}',
        }
        _logger.error(f'{e}')
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/api/tasks/{task_id}/sample/', description='Input a SUCCESS task_id and table_names to get the sampling result.'
                                                     'If you have no clue of task_id or table_names check the  '
                                                     '/api/tasks/{task_id} or /api/tasks/ before to gain such information ')
async def sample_result(task_id: str):
    if len(task_id) != 32:
        err_info = {
            "error_code": 400,
            "error_message": f'{task_id} is not in proper format, expect 32 digits get {len(task_id)} digits'
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    tb_list = get_table_info(task_id)



    if not tb_list:
        if query_state_by_id(task_id).get('prod_stat') == 'no_data':
            err_info = {
                "error_code": 404,
                "error_message": f"there is no data processed in task {task_id}"
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

        err_info = {
            "error_code": 404,
            "error_message": f"result table is not found, plz wait for awhile to retry it"
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    q = ''
    for i in range(len(tb_list)):
        output_tb_name = f'{tb_list[i]}'
        query = get_sample_query(task_id, output_tb_name,
                                 TaskSampleResult.NUMBER)
        q += query
        if i != len(tb_list) - 1:
            q += ' UNION ALL '
        else:
            pass

    try:
        result = scrap_data_to_dict(q, TaskSampleResult.OUTPUT_SCHEMA)

        if len(result) == 0:
            err_info = {
                "error_code": 404,
                "error_message": "empty result, probably wrong combination of task_id and table_name, "
                                 "please check table state or use /api/tasks/{task_id} first"
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
            "error_message": f"Cannot scrape data from result tables. Additional error message: {e}"
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.post('/api/tasks/abort/', description='aborting a task no matter it is executing')
async def abort_task(abort_request_body: AbortionConfig):
    config = abort_request_body.__dict__
    task_id = config.get('TASK_ID', None)

    if len(task_id) != 32:
        err_info = {
            "error_code": 400,
            "error_message": f'{task_id} is not in proper format, expect 32 digits get {len(task_id)} digits'
        }
        _logger.error(err_info)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        send_break_signal_to_state(task_id)
        err_info = {
            "error_code": 200,
            "error_message" : f"successfully send break status to task {task_id} in state"
        }
    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"failed to send break status to task, additional error message: {e}"
        }

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))


@app.post('/api/tasks/dump/', description='run dump workflow with task_id')
async def dump_tasks(dump_request_body: DumpConfig):
    config = dump_request_body.__dict__

    if not config.get('task_ids') or len(config.get('task_ids')) == 0:
        err_info = {
            "error_code": 404,
            "error_message": f"task_ids cannot be null or empty in dump_tasks"
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    try:
        dump_result.apply_async(kwargs=config)
        err_info = {
            "error_code": 200,
            "error_message": config
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

    except Exception as e:
        err_info = {
            "error_code": 500,
            "error_message": f"task failed because of {e}"
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_info))

@app.get('/', description='redirect to open API docs')
def redirect_to_docs():
    return RedirectResponse('/docs')


if __name__ == '__main__':
    uvicorn.run(app, host=configuration.API_HOST, debug=True)


