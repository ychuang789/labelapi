from fastapi import APIRouter, Depends

import uuid

from fastapi import  status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import training, testing
from settings import DatabaseConfig, ModelingAbort, ModelingTrainingConfig, ModelingTestingConfig
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
def model_training(training_config: ModelingTrainingConfig):
    task_id = uuid.uuid1().hex

    config = training_config.__dict__
    config.update({'task_id':task_id})

    create_model_table()

    try:
        training.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))
        ModelingWorker.add_task_info(task_id=task_id, model_name=config['MODEL_TYPE'],
                                     predict_type=config['PREDICT_TYPE'], model_path=config['MODEL_PATH'],
                                     job_id=config['MODEL_JOB_ID'])
    except Exception as e:
        err_msg = f'failed to add training task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))
    # return JSONResponse(status_code=status.HTTP_200_OK, content=model.__class__.__name__)

@router.post('/test/', description='testing a model')
def model_testing(testing_config: ModelingTestingConfig):

    condition = {'model_job_id': testing_config.MODEL_JOB_ID}
    result = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                        **ConnectionConfigGenerator.rd2_database(schema=DatabaseConfig.OUTPUT_SCHEMA))
    if not result:
        err_msg = f'Model is not train or prepare yet, execute training API first'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    else:
        task_id = result['task_id']

    config = testing_config.__dict__
    config.update({'task_id': task_id})

    create_model_table()

    try:
        testing.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))
        ModelingWorker.add_task_info(task_id=task_id, model_name=config['MODEL_TYPE'],
                                     predict_type=config['PREDICT_TYPE'], model_path=config['MODEL_PATH'],
                                     ext_test=True)
    except Exception as e:
        err_msg = f'failed to add testing task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@router.get('/{model_job_id}')
def model_status(model_job_id: int):

    condition = {'model_job_id': model_job_id}
    result = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                      **ConnectionConfigGenerator.rd2_database(schema=DatabaseConfig.OUTPUT_SCHEMA))
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

@router.get('/{model_job_id}/report/')
def model_report(model_job_id):

    condition = {'model_job_id': model_job_id, 'model_report': 'report'}
    result = DBConnection.execute_query(query=QueryManager.get_model_query(**condition),
                                        **ConnectionConfigGenerator.rd2_database(schema=DatabaseConfig.OUTPUT_SCHEMA))
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

@router.post('/abort/')
def model_abort(abort_request_body: ModelingAbort):
    model_job_id = abort_request_body.MODEL_JOB_ID
    try:
        status_changer(model_job_id)
        err_msg = f'{model_job_id} is successfully aborted'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f'{model_job_id} abortion failed with {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
