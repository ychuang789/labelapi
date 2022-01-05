from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter

import json
import uuid

from fastapi import  status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import preparing, testing
from settings import DatabaseConfig, ModelingAbort, ModelingTrainingConfig, ModelingTestingConfig, ModelingDelete
from workers.orm_worker import ORMWorker

router = APIRouter(prefix='/model',
                   tags=['model'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )

@router.post('/prepare/', description='preparing a model')
def model_preparing(training_config: ModelingTrainingConfig):
    task_id = uuid.uuid1().hex

    config = training_config.__dict__


    try:
        preparing.apply_async(args=(task_id,), kwargs=config, task_id=task_id, queue=config.get('QUEUE'))
    except Exception as e:
        err_msg = f'failed to add training task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    config.update({'task_id': task_id})
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@router.post('/test/', description='testing a model')
def model_testing(testing_config: ModelingTestingConfig):

    config = testing_config.__dict__

    try:
        testing.apply_async(args=(config.get('MODEL_JOB_ID'),), kwargs=config, queue=config.get('QUEUE'))
    except Exception as e:
        err_msg = f'failed to add testing task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@router.get('/{model_job_id}')
def model_status(model_job_id: int):
    conn = ORMWorker(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        err_msg = conn.get_status(model_job_id=model_job_id)
        result = {c.name: (getattr(err_msg, c.name) if not isinstance(getattr(err_msg, c.name), datetime)
                                      else getattr(err_msg,c.name).strftime("%Y-%m-%d %H:%M:%S"))
                             for c in err_msg.__table__.columns}
    except AttributeError:
        result = f'model_job task: {model_job_id} is not exists'
    except Exception as e:
        result = f'failed to get status since {e}'
    finally:
        conn.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

@router.get('/{model_job_id}/report/')
def model_report(model_job_id):
    conn = ORMWorker(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        err_msg = conn.get_report(model_job_id=model_job_id)

        result = []
        for err in err_msg:
            _result_dict = {}
            for c in err.__table__.columns:
                key = c.name
                if isinstance(getattr(err, c.name), datetime):
                    value = getattr(err, c.name).strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(getattr(err, c.name), Decimal):
                    value = float(getattr(err, c.name))
                else:
                    value = getattr(err, c.name)
                _result_dict.update({key: value})
            result.append(_result_dict)
    except AttributeError:
        result = f'model_job task: {model_job_id} is not exists'
    except Exception as e:
        result = f'failed to get report since {e}'
    finally:
        conn.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))

@router.post('/abort/')
def model_abort(abort_request_body: ModelingAbort):
    model_job_id = abort_request_body.MODEL_JOB_ID
    conn = ORMWorker(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        msg = conn.status_changer(model_job_id=model_job_id)
        err_msg = f'{model_job_id} is successfully aborted, additional message: {msg}'
    except Exception as e:
        err_msg = f'{model_job_id} abortion is failed since {e}'
    finally:
        conn.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

@router.delete('/delete/')
def model_delete(deletion: ModelingDelete):
    delete_model_job_id = deletion.MODEL_JOB_ID
    conn = ORMWorker(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        msg = conn.delete_record(model_job_id=delete_model_job_id)
        err_msg = f'{delete_model_job_id} is successfully deleted, additional message: {msg}'
    except Exception as e:
        err_msg = f'{delete_model_job_id} deletion is failed since {e}'
    finally:
        conn.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))