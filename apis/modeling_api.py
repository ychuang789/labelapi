from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter
import uuid

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import modeling_task, testing
from settings import DatabaseConfig, ModelingAbort, ModelingTrainingConfig, ModelingTestingConfig, ModelingDelete
from workers.orm_core.model_operation import ModelingCRUD

router = APIRouter(prefix='/models',
                   tags=['models'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )

@router.post('/prepare/', description='preparing a model')
def model_preparing(body: ModelingTrainingConfig):
    task_id = uuid.uuid1().hex

    config = body.__dict__

    try:
        modeling_task.apply_async(
            args=(
                task_id,
                body.MODEL_JOB_ID,
                body.MODEL_TYPE,
                body.PREDICT_TYPE,
                body.DATASET_NO,
                body.DATASET_DB
            ),
            kwargs=body.MODEL_INFO,
            task_id=task_id,
            queue=body.QUEUE
        )

    except Exception as e:
        err_msg = f'failed to add training task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    config.update({'task_id': task_id})
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@router.post('/test/', description='testing a model')
def model_testing(body: ModelingTestingConfig):

    config = body.__dict__

    try:
        testing.apply_async(
            args=(
                body.MODEL_JOB_ID,
                body.MODEL_TYPE,
                body.PREDICT_TYPE,
                body.DATASET_NO,
                body.DATASET_DB
            ),
            kwargs=config,
            queue=body.QUEUE
        )

    except Exception as e:
        err_msg = f'failed to add testing task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(config))

@router.get('/{model_job_id}')
def model_status(model_job_id: int):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        err_msg = conn.model_get_status(model_job_id=model_job_id)
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
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)

    try:
        temp_result = conn.model_get_report(model_job_id=model_job_id)

        result = []
        for t in temp_result:
            _result_dict = {}
            for c in t.__table__.columns:
                key = c.name
                if isinstance(getattr(t, c.name), datetime):
                    value = getattr(t, c.name).strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(getattr(t, c.name), Decimal):
                    value = float(getattr(t, c.name))
                else:
                    value = getattr(t, c.name)
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
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        msg = conn.model_status_changer(model_job_id=model_job_id)
        err_msg = f'{model_job_id} is successfully aborted, additional message: {msg}'
    except Exception as e:
        err_msg = f'{model_job_id} abortion is failed since {e}'
    finally:
        conn.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

@router.delete('/delete/')
def model_delete(deletion: ModelingDelete):
    delete_model_job_id = deletion.MODEL_JOB_ID
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        msg = conn.model_delete_record(model_job_id=delete_model_job_id)
        err_msg = f'{delete_model_job_id} is successfully deleted, additional message: {msg}'
    except Exception as e:
        err_msg = f'{delete_model_job_id} deletion is failed since {e}'
    finally:
        conn.dispose()

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
