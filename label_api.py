import uuid
from typing import List

import uvicorn
from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse

from celery.result import AsyncResult
from utils.database_core import scrap_data_to_df
from utils.helper import get_logger
from utils.run_label_task import read_from_dir
from utils.selections import ModelType, PredictTarget

from celery_worker import label_data

_logger = get_logger('label_API')

app = FastAPI(title="Labeling Task API",
              description="For helping AS department to labeling the data")

model_list = [i.value for i in ModelType]
predict_list = [i.value for i in PredictTarget]
year_list = [i for i in range(2018,2022)]
month_list = [i for i in range(1,13)]
table_list = ['predicting_jobs_predictingresult']


@app.post('/create_tasks/')
async def create(model_type: str = Query(..., enum=model_list),
                 predict_type: str = Query(..., enum=predict_list),
                 start_year: int = Query(..., enum=year_list),
                 start_month: int = Query(..., enum=month_list),
                 end_year: int = Query(..., enum=year_list),
                 end_month: int = Query(..., enum=month_list),
                 target_table: str = Query(..., enum=table_list)):

    if start_year < end_year:
        pass
    elif start_year > end_year:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=f'start year must be smaller or equal to end year.')
    else:
        if start_month > end_month:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content=f'start month must be smaller or equal to end month in same year.')

    task_id = uuid.uuid1().hex
    setting = {"task_id": task_id,
               "model_type": model_type,
               "predict_type": predict_type,
               "date_range": f"{start_year}/{start_month} - {end_year}/{end_month}",
               "target_table": target_table}


    _logger.info('Preparing data...')
    try:
        pattern = read_from_dir(model_type, predict_type)
    except:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=f'rule file is not found.')

    query = f"SELECT * FROM {target_table} " \
            f"WHERE applied_feature='author' " \
            f"AND created_at >= '{start_year}-{str(start_month).zfill(2)}-01 00:00:00'" \
            f"AND created_at <= '{end_year}-{str(end_month).zfill(2)}-31 23:59:59'"

    _logger.info('start the labeling worker ...')
    result = label_data.apply_async((task_id, query, pattern, model_type, predict_type))

    setting.update({'task_id': f'{task_id};{result.id}'})
    _logger.info(f'API configuration: {setting}')

    return JSONResponse(status_code=status.HTTP_200_OK, content=setting)


@app.post('/task_list/')
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

@app.post('/check_status/')
async def check_status(_id: str = Query(...)):
    try:
        _result = AsyncResult(_id.split(';')[1], app=label_data)
        return JSONResponse(status_code=status.HTTP_200_OK, content=_result.status)
    except:
        err_msg = f'task id is not exist, plz re-check the task id.'
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=err_msg)

@app.post('/sample_result/')
async def sample_result(_id: str = Query(...),
                        table: str = Query(...),
                        order_column: str = Query(...),
                        number: int = Query(...),
                        offset: int = Query(...)):

    query = f"SELECT * FROM {table} WHERE task_id = '{_id.split(';')[0]}' " \
            f"AND id >= (SELECT id FROM {table} ORDER BY {order_column} LIMIT {offset},1) " \
            f"LIMIT {number}"

    schema = 'audience_result'
    try:
        result = scrap_data_to_df(_logger, query, schema=schema)

        return JSONResponse(status_code=status.HTTP_200_OK, content=result.to_json())
    except:
        err_msg = f'invalid sql query, plz re-check it.'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err_msg)




if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', debug=True)


