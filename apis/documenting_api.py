import os

from fastapi import APIRouter, UploadFile, File

from fastapi import status
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse, FileResponse

from apis.input_class.documenting_input import DocumentRequest, DatasetRequest, RulesRequest
from celery_worker import export_document_file, import_document_file
from definition import SAVE_DOCUMENT_FOLDER
from settings import DatabaseConfig
from utils.general_helper import get_logger
from workers.orm_core.document_operation import DocumentCRUD

router = APIRouter(prefix='/documents',
                   tags=['documents'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )

logger = get_logger('debug')


@router.get('/', description='render all document tasks')
def document_render():
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        temp_result = conn.task_render()
        result = [conn.orm_cls_to_dict(t) for t in temp_result]
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
        task = conn.task_create(task_id=task_id, **body.dict())
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, task {task.task_id} created')
    except Exception as e:
        err_msg = f'failed to add task since {type(e).__name__}:{e}'
        logger.info(err_msg)
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
        stored_data = body.dict(exclude_none=True)
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
        dataset = conn.dataset_create(task_id=task_id, **body.dict())
        return JSONResponse(status_code=status.HTTP_200_OK, content=f'OK, data_id {dataset.id} is created')
    except Exception as e:
        err_msg = f'failed to create a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.get('/{task_id}/dataset', description='render the task dataset')
def dataset_render(task_id: str):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        temp_dataset = conn.dataset_render(task_id=task_id)
        dataset = [conn.orm_cls_to_dict(data) for data in temp_dataset]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(dataset))
    except Exception as e:
        err_msg = f'failed to render task {task_id} dataset since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))


@router.get('/dataset/{dataset_id}', description='get single data')
def dataset_retrieve(dataset_id: int):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        temp_data = conn.dataset_get(dataset_id=dataset_id)
        data = conn.orm_cls_to_dict(temp_data)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=jsonable_encoder(data))
    except Exception as e:
        err_msg = f'failed to update a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.patch('/dataset/{dataset_id}/update', description='update single data')
def dataset_update(dataset_id: int, body: DatasetRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        dataset = conn.dataset_update(dataset_id=dataset_id, **body.dict(exclude_none=True))
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, data_id {dataset.id} is updated')
    except Exception as e:
        err_msg = f'failed to update a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/dataset/{dataset_id}/delete', description='delete single data')
def dataset_delete(dataset_id: int):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.dataset_delete(dataset_id=dataset_id)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, data_id {dataset_id} is deleted')
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
        rule = conn.rule_create(task_id=task_id, **body.dict())
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=f'OK, rule_id {rule.id} is created')
    except Exception as e:
        err_msg = f'failed to create a rule since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.get('/{task_id}/rules', description='render the task rules')
def rules_render(task_id: str):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        temp_rules = conn.rule_render(task_id=task_id)
        rules = [conn.orm_cls_to_dict(rule) for rule in temp_rules]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(rules))
    except Exception as e:
        err_msg = f'failed to render task {task_id} rules since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))


@router.get('/rules/{rule_id}', description='get single rule')
def rule_retrieve(rule_id: int):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        temp_data = conn.rule_get(rule_id=rule_id)
        data = conn.orm_cls_to_dict(temp_data)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=jsonable_encoder(data))
    except Exception as e:
        err_msg = f'failed to update a data since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.patch('/rules/{rule_id}/update', description='update single data')
def rules_update(rule_id: int, body: RulesRequest):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        rule = conn.rule_update(rule_id=rule_id, **body.dict(exclude_none=True))
        return JSONResponse(status_code=status.HTTP_200_OK,
                     content=f'OK, rule_id {rule.id} is updated')
    except Exception as e:
        err_msg = f'failed to update a rule since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.delete('/rules/{rule_id}/delete', description='delete single data')
def rule_delete(rule_id: int):
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        conn.rule_delete(rule_id=rule_id)
        JSONResponse(status_code=status.HTTP_200_OK,
                     content=f'OK, rule_id {rule_id} is deleted')
    except Exception as e:
        err_msg = f'failed to delete a rule since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        conn.dispose()


@router.post('/{task_id}/upload', description='upload and overwrite dataset')
def dataset_upload(task_id: str, overwrite: str, file: UploadFile = File(...)):
    try:
        filepath = os.path.join(SAVE_DOCUMENT_FOLDER, file.filename)
        with open(filepath, 'wb+') as file_object:
            file_object.write(file.file.read())

        import_document_file.apply_async(
            args=(
                task_id,
                overwrite,
                filepath
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
    conn = DocumentCRUD(connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO)
    try:
        result = conn.download_checker(task_id=task_id)
        if isinstance(result, dict) and result.get('file'):
            return FileResponse(status_code=status.HTTP_200_OK, path=result.get('file'), filename=f'{task_id}.csv')
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
    except Exception as e:
        err_msg = f'failed to download file since {type(e).__name__}:{e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
