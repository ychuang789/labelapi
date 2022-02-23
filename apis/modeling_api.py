import os

from fastapi import APIRouter, UploadFile, File

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse

from celery_worker import modeling_task, testing, import_model
from definition import MODEL_IMPORT_FOLDER
from settings import DatabaseConfig
from apis.input_class.modeling_input import ModelingAbort, ModelingTrainingConfig, ModelingTestingConfig, \
    ModelingDelete, TermWeightsAdd, TermWeightsUpdate, TermWeightsDelete
from utils.data.data_download import find_file, term_weight_to_file
from utils.exception_manager import ModelTypeError, TWMissingError
from workers.orm_core.model_operation import ModelingCRUD

router = APIRouter(prefix='/models',
                   tags=['models'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )


@router.post('/prepare/', description='preparing a model')
def model_preparing(body: ModelingTrainingConfig):
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


@router.get('/{task_id}', description='get the modeling task progress and information')
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


@router.get('/{task_id}/report/', description='get the specific modeling task report')
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


@router.post('/abort/', description='abort a modeling task')
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


@router.delete('/delete/', description='delete a modeling task')
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


@router.post('/{task_id}/import_model/', description='external import term weights from local files')
def model_import(task_id, file: UploadFile = File(...)):
    upload_filepath = os.path.join(MODEL_IMPORT_FOLDER, file.filename)

    try:
        with open(upload_filepath, 'wb+') as file_object:
            file_object.write(file.file.read())
        import_model.apply_async(
            args=(upload_filepath, file.filename, task_id),
            queue="queue2"
        )
        err_msg = f"successfully save {file.filename}"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    except Exception as e:
        err_msg = f"failed to save {file.filename} since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))


# @router.get('/{task_id}/import_model/{upload_job_id}')
# def get_import_model_status(task_id: str, upload_job_id: int):
#     conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
#     try:
#         result = conn.get_upload_model_status(upload_job_id=upload_job_id)
#         if not result:
#             result = f'import_model task: {task_id}_{upload_job_id} is not exists'
#             return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(result))
#         else:
#             return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
#     except AttributeError:
#         result = f'import_model task: {task_id}_{upload_job_id} is not exists'
#         return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(result))
#     except Exception as e:
#         result = f'failed to get status since {e}'
#         return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(result))
#     finally:
#         conn.dispose()


@router.get('/{task_id}/eval_details/{report_id}/{limit}', description='get the evaluation detail row data by limit')
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


@router.get('/{task_id}/false_predict/{report_id}/{limit}', description='get the false predicting row data by limit')
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


@router.get('/{task_id}/true_predict/{report_id}/{limit}', description='get the true predicting row data by limit')
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


@router.get('/download_details/{task_id}/{dataset_type}', description='download the row prediction detail file')
def download_details(task_id: str, dataset_type: str):
    try:
        filename, filepath = find_file(task_id, dataset_type)
        if filename and filepath:
            return FileResponse(status_code=status.HTTP_200_OK, path=filepath, filename=filename)
        else:
            results = f"There are no eval details for {task_id} {dataset_type} set"
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(results))
    except Exception as e:
        results = f"failed to get eval details since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(results))


@router.put('/term_weight/add', description='add a new row of term weight')
def term_weight_add(body: TermWeightsAdd):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.add_term_weight(task_id=body.TASK_ID,
                             label=body.LABEL,
                             term=body.TERM,
                             weight=body.WEIGHT)
        err_msg = f"term weight is successfully added"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except AttributeError:
        err_msg = f"Task {body.TASK_ID} is not prepared or not trained yet"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    except ModelTypeError:
        err_msg = f"Task {body.TASK_ID} model is not supported term weight CURD"
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"{e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.get('/{task_id}/term_weight', description='get all term weights data from a modeling task')
def get_term_weights(task_id: str):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        result = conn.get_term_weight_set(task_id=task_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except AttributeError:
        err_msg = f"Task {task_id} is not prepared or not trained yet"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    except ModelTypeError:
        err_msg = f"Task {task_id} model is not supported term weight CURD"
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"{e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.post('/term_weight/update', description='update a term weight row')
def term_weight_update(body: TermWeightsUpdate):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.update_term_weight(tw_id=body.TERM_WEIGHT_ID,
                                label=body.LABEL,
                                term=body.TERM,
                                weight=body.WEIGHT)
        err_msg = f"Done, term_weight {body.TERM_WEIGHT_ID} is updated"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    except TWMissingError:
        err_msg = f"Term weight {body.TERM_WEIGHT_ID} is not found"
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"{e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/term_weight/delete', description='delete a term weight row')
def term_weight_delete(body: TermWeightsDelete):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.delete_term_weight(tw_id=body.TERM_WEIGHT_ID)
        err_msg = f"Done, Term weight {body.TERM_WEIGHT_ID} is deleted"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except TWMissingError:
        err_msg = f"Term weight {body.TERM_WEIGHT_ID} is not found"
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"{e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.get('/{task_id}/term_weight/download', description='download term weight query set of a modeling task')
def term_weight_download(task_id: str):
    conn = ModelingCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    filename = f"{task_id}_term_weight"
    try:
        result = conn.get_term_weight_set(task_id=task_id)
        filepath = term_weight_to_file(term_weight_set=result['data'], filename=filename)
        return FileResponse(status_code=status.HTTP_200_OK, path=filepath, filename=filename + '.csv')
    except AttributeError:
        err_msg = f"Task {task_id} is not prepared or not trained yet"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"{e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()
