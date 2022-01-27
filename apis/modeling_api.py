import os
from fastapi import APIRouter, UploadFile, File

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from celery_worker import modeling_task, testing
from definition import MODEL_IMPORT_FOLDER
from settings import DatabaseConfig, ModelingAbort, ModelingTrainingConfig, ModelingTestingConfig, ModelingDelete
from workers.orm_core.model_operation import ModelingCRUD

router = APIRouter(prefix='/models',
                   tags=['models'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )


@router.post('/prepare/', description='preparing a model')
def model_preparing(body: ModelingTrainingConfig):
    # task_id = uuid.uuid1().hex
    try:
        modeling_task.apply_async(
            args=(
                body.TASK_ID,
                body.MODEL_TYPE,
                body.PREDICT_TYPE,
                body.DATASET_NO,
                body.DATASET_DB
            ),
            kwargs=body.MODEL_INFO,
            task_id=body.TASK_ID,
            queue=body.QUEUE
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(body.TASK_ID))
    except Exception as e:
        err_msg = f'failed to add training task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))


@router.post('/test/', description='testing a model')
def model_testing(body: ModelingTestingConfig):
    try:
        testing.apply_async(
            args=(
                body.TASK_ID,
                body.MODEL_TYPE,
                body.PREDICT_TYPE,
                body.DATASET_NO,
                body.DATASET_DB
            ),
            kwargs=body.MODEL_INFO,
            queue=body.QUEUE
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(body.TASK_ID))
    except Exception as e:
        err_msg = f'failed to add testing task info to modeling_status since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))


@router.get('/{task_id}')
def model_status(task_id: str):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        result = conn.model_get_status(task_id=task_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except AttributeError:
        result = f'model_job task: {task_id} is not exists'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(result))
    except Exception as e:
        result = f'failed to get status since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(result))
    finally:
        conn.dispose()


@router.get('/{task_id}/report/')
def model_report(task_id: str):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)

    try:
        result = conn.model_get_report(task_id=task_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except AttributeError:
        result = f'model_job task: {task_id} is not exists'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(result))
    except Exception as e:
        result = f'failed to get report since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(result))
    finally:
        conn.dispose()


@router.post('/abort/')
def model_abort(body: ModelingAbort):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        msg = conn.model_status_changer(task_id=body.TASK_ID)
        err_msg = f'{body.TASK_ID} is successfully aborted, additional message: {msg}'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f'{body.TASK_ID} abortion is failed since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/delete/')
def model_delete(body: ModelingDelete):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.model_delete_record(task_id=body.TASK_ID)
        err_msg = f'{body.TASK_ID} is successfully deleted'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f'{body.TASK_ID} deletion is failed since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.post('/import_model/')
def model_import(file: UploadFile = File(...)):
    upload_filepath = os.path.join(MODEL_IMPORT_FOLDER, file.filename)
    try:
        with open(upload_filepath, 'wb+') as file_object:
            file_object.write(file.file.read())
        err_msg = f"save {file.filename} to {MODEL_IMPORT_FOLDER}"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"failed to save {file.filename} since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))




