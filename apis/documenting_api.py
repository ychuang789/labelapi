import os.path

from celery.result import AsyncResult
from fastapi import APIRouter, UploadFile, File

from fastapi import status
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse, FileResponse

from apis.input_class.documenting_input import DocumentRequest, DatasetRequest, RulesRequest
from celery_worker import export_document_file, import_document_file
from definition import SAVE_DOCUMENT_FOLDER
from settings import DatabaseConfig
from workers.orm_core.document_operation import DocumentCRUD

router = APIRouter(prefix='/documents',
                   tags=['documents'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )


@router.get('/', description='render all document tasks')
def document_render():
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        result = conn.task_render()
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        err_msg = f'failed to render tasks since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.post('/{task_id}/add', description='add a document task')
def document_add(task_id: str, body: DocumentRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        task = conn.task_create(task_id=task_id, **body.__dict__)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, task {task.task_id} created')
    except Exception as e:
        err_msg = f'failed to add task since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.get('/{task_id}', description='retrieve a task')
def document_retrieve(task_id: str):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        result = conn.orm_cls_to_dict(conn.task_retrieve(task_id=task_id))
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        err_msg = f'failed to retrieve a task since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.patch('/{task_id}/update', description='update a task')
def document_update(task_id: str, body: DocumentRequest):
    """https://fastapi.tiangolo.com/tutorial/body-updates/#using-pydantics-exclude_unset-parameter"""
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        stored_data = body.__dict__
        # stored_model = DocumentRequest(**stored_data)
        # update_data = body.dict(exclude_unset=True)
        # updated_data = stored_model.copy(update=update_data)
        task = conn.task_update(task_id=task_id, **stored_data)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, task {task.task_id} patched')
    except Exception as e:
        err_msg = f'failed to update a task since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/{task_id}/delete', description='delete a task')
def document_delete(task_id: str):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.task_delete(task_id=task_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content='OK')
    except Exception as e:
        err_msg = f'failed to delete a task since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.post('/{task_id}/dataset/add', description='add single data')
def dataset_add(task_id: str, body: DatasetRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        dataset = conn.dataset_create(task_id=task_id, **body.__dict__)
        return JSONResponse(status_code=status.HTTP_200_OK, content=f'OK, data {dataset.id} is created')
    except Exception as e:
        err_msg = f'failed to create a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.patch('/{task_id}/dataset/{dataset_id}/update', description='update single data')
def dataset_update(task_id: str, dataset_id: int, body: DatasetRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        dataset = conn.dataset_update(task_id=task_id, dataset_id=dataset_id, **body.__dict__)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, data {dataset.id} is updated')
    except Exception as e:
        err_msg = f'failed to update a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/{task_id}/dataset/{dataset_id}/delete', description='delete single data')
def dataset_delete(task_id: str, dataset_id: int):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.dataset_delete(task_id=task_id, dataset_id=dataset_id)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, data {dataset_id} is deleted')
    except Exception as e:
        err_msg = f'failed to delete a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()
    pass


@router.post('/{task_id}/rules/add', description='add single rule')
def rule_add(task_id: str, body: RulesRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        rule = conn.rule_create(task_id=task_id, **body.__dict__)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, rule {rule.id} is created')
    except Exception as e:
        err_msg = f'failed to create a rule since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.patch('/{task_id}/rules/{rule_id}/update', description='update single data')
def dataset_update(task_id: str, rule_id: int, body: RulesRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        rule = conn.rule_update(task_id=task_id, rule_id=rule_id, **body.__dict__)
        JSONResponse(status_code=status.HTTP_200_OK,
                     content=f'OK, rule {rule.id} is updated')
    except Exception as e:
        err_msg = f'failed to update a rule since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/{task_id}/rules/{rule_id}/delete', description='delete single data')
def dataset_delete(task_id: str, rule_id: int):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.rule_delete(task_id=task_id, rule_id=rule_id)
        JSONResponse(status_code=status.HTTP_200_OK,
                     content=f'OK, rule {rule_id} is deleted')
    except Exception as e:
        err_msg = f'failed to delete a rule since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.post('/{task_id}/upload/{overwrite}', description='upload and overwrite dataset')
def dataset_upload(task_id: str, overwrite: bool, file: UploadFile = File(...)):
    try:
        import_document_file.apply_async(
            args=(
                task_id,
                overwrite,
                file
            ),
            queue='queue3'
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content='OK')
    except Exception as e:
        err_msg = f'failed to upload file since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))


@router.post('/{task_id}/download', description='post download dataset')
def dataset_download(task_id: str):
    try:
        export_document_file.apply_async(
            args=(
                task_id,
            ),
            task_id=task_id,
            queue='queue3'
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=f'{task_id}')
    except Exception as e:
        err_msg = f'failed to download file since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))


@router.get('/{task_id}/download', description='get download dataset')
def dataset_download(task_id: str):
    try:
        filename = f"{task_id}.csv"
        file_path = os.path.join(SAVE_DOCUMENT_FOLDER, filename)
        task = AsyncResult(task_id)
        ready = task.ready()
        if ready:
            return FileResponse(status_code=status.HTTP_200_OK, path=file_path, filename=filename)
        return JSONResponse(status_code=status.HTTP_200_OK, content=f'{task_id} not ready')
    except Exception as e:
        err_msg = f'failed to download file since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
