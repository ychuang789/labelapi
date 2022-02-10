import os
from fastapi import APIRouter, UploadFile, File

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse

from celery_worker import modeling_task, testing, import_model
from definition import MODEL_IMPORT_FOLDER
from settings import DatabaseConfig, ModelingAbort, ModelingTrainingConfig, ModelingTestingConfig, ModelingDelete, \
    ModelingUpload
from utils.data.data_download import find_file
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
        result = conn.get_status(task_id=task_id)
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
        result = conn.get_report(task_id=task_id)
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
        msg = conn.status_changer(task_id=body.TASK_ID)
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
        conn.delete_record(task_id=body.TASK_ID)
        err_msg = f'{body.TASK_ID} is successfully deleted'
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f'{body.TASK_ID} deletion is failed since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.put('/import_model/')
def model_import(body: ModelingUpload, file: UploadFile = File(...)):
    upload_filepath = os.path.join(MODEL_IMPORT_FOLDER, file.filename)

    try:
        with open(upload_filepath, 'wb+') as file_object:
            file_object.write(file.file.read())
        import_model.apply_async(
            args=(file.file, file.filename, body.TASK_ID, body.UPLOAD_JOB_ID),
            queue=body.QUEUE
        )
        err_msg = f"successfully save {file.filename}"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    except Exception as e:
        err_msg = f"failed to save {file.filename} since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))


@router.get('/{task_id}/import_model/{upload_job_id}')
def get_import_model_status(task_id: str, upload_job_id: int):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        result = conn.get_upload_model_status(upload_job_id=upload_job_id)
        if not result:
            result = f'import_model task: {task_id}_{upload_job_id} is not exists'
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(result))
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except AttributeError:
        result = f'import_model task: {task_id}_{upload_job_id} is not exists'
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(result))
    except Exception as e:
        result = f'failed to get status since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(result))
    finally:
        conn.dispose()


@router.get('/{task_id}/eval_details/{report_id}/{limit}')
def get_eval_details(task_id: str, report_id: int, limit: int):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        results = conn.get_eval_details(task_id=task_id, report_id=report_id, limit=limit)
        if not results:
            results = f"There are no eval details for task {task_id}, report {report_id}"
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(results))
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(results))
    except Exception as e:
        results = f"failed to get eval details since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(results))
    finally:
        conn.dispose()


@router.get('/{task_id}/false_predict/{report_id}/{limit}')
def get_eval_details_false_prediction(task_id: str, report_id: int, limit: int):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        results = conn.get_eval_details_false_prediction(task_id=task_id, report_id=report_id, limit=limit)
        if not results:
            results = f"There are no eval details for task {task_id}, report {report_id}"
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(results))
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(results))
    except Exception as e:
        results = f"failed to get eval details since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(results))
    finally:
        conn.dispose()


@router.get('/{task_id}/true_predict/{report_id}/{limit}')
def get_eval_details_true_prediction(task_id: str, report_id: int, limit: int):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        results = conn.get_eval_details_true_prediction(task_id=task_id, report_id=report_id, limit=limit)
        if not results:
            results = f"There are no eval details for task {task_id}, report {report_id}"
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(results))
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(results))
    except Exception as e:
        results = f"failed to get eval details since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(results))
    finally:
        conn.dispose()


@router.get('/{report_id}/download_details/')
def download_details(report_id: int):
    try:
        filename, filepath = find_file(report_id)
        if filename and filepath:
            return FileResponse(status_code=status.HTTP_200_OK, path=filepath, filename=filename)
        else:
            results = f"There are no eval details for report {report_id}"
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(results))
    except Exception as e:
        results = f"failed to get eval details since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(results))





