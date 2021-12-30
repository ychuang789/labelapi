from fastapi import APIRouter, Depends

import uuid

from fastapi import  status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import training, testing
from settings import DatabaseConfig, ModelingAbort, ModelingConfig
from utils.connection_helper import DBConnection, QueryManager, ConnectionConfigGenerator
from utils.helper import  uuid_validator
from utils.model_core import ModelingWorker
from utils.model_table_creator import create_model_table, status_changer
from dependencies import get_token_header

router = APIRouter(prefix='/model',
                   tags=['model'],
                   dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )

@router.post('/train/', description='training a model and save it')
def model_training(training_config: ModelingConfig):
    task_id = uuid.uuid1().hex

    config = training_config.__dict__
    config.update({'task_id':task_id})

    create_model_table()

    try:
        training.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))
        ModelingWorker.add_task_info(task_id=task_id, model_name=config['MODEL_TYPE'],
                                     predict_type=config['PREDICT_TYPE'], model_path=config['MODEL_PATH'])
    except Exception as e:
        err_msg = f'failed to add training task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))
    # return JSONResponse(status_code=status.HTTP_200_OK, content=model.__class__.__name__)

@router.post('/test/', description='testing a model')
def model_testing(testing_config: ModelingConfig):
    task_id = uuid.uuid1().hex

    config = testing_config.__dict__
    config.update({'task_id': task_id})

    create_model_table()

    try:
        testing.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))
        ModelingWorker.add_task_info(task_id=task_id, model_name=config['MODEL_TYPE'],
                                     predict_type=config['PREDICT_TYPE'], model_path=config['MODEL_PATH'])
    except Exception as e:
        err_msg = f'failed to add testing task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@router.get('/{task_id}')
def model_status(task_id: str):
    if not uuid_validator(task_id):
        err_msg = f'''{task_id} is not in a proper 32-digit uuid format'''
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    condition = {'task_id': task_id}
    result = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                      **ConnectionConfigGenerator.rd2_database(schema=DatabaseConfig.OUTPUT_SCHEMA))
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

@router.get('/api/models/{task_id}/report/')
def model_report(task_id):
    if not uuid_validator(task_id):
        err_msg = f'''{task_id} is not in a proper 32-digit uuid format'''
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    condition = {'task_id': task_id, 'model_report': 'report'}
    result = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                        **ConnectionConfigGenerator.rd2_database(schema=DatabaseConfig.OUTPUT_SCHEMA))
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

@router.post('/abort/')
def model_abort(abort_request_body: ModelingAbort):

    if not uuid_validator(task_id := abort_request_body.task_id):
        err_msg = f'''{task_id} is not in a proper 32-digit uuid format'''
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    try:
        status_changer(abort_request_body.task_id)
        err_msg = f'{task_id} is successfully aborted'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f'{task_id} abortion failed with {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
