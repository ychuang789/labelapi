from fastapi import APIRouter, UploadFile, File, Request

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from pydantic import ValidationError

from apis.input_class.documenting_input import DocumentAddRequest

router = APIRouter(prefix='/documents',
                   tags=['documents'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )


# @router.exception_handler(RequestValidationError)
# def request_validation_exception_handler(request: Request, exc: RequestValidationError):
#     pass


@router.post('/add', description='add a document task')
def document_add(body: DocumentAddRequest):
    try:
        # todo: write data into database
        return JSONResponse(status_code=status.HTTP_200_OK, content='OK')
    except Exception as e:
        err_msg = f'failed to add task since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))


@router.get('/{task_id}', description='retrieve a task')
def document_retrieve(task_id: str):
    pass


@router.put('/{task_id}/update', description='update a task')
def document_update(task_id: str):
    pass


@router.delete('/{task_id}/delete', description='delete a task')
def document_delete(task_id: str):
    pass


@router.post('/{task_id}/dataset/add', description='add single data')
def dataset_add(task_id: str, body):
    pass


@router.get('/{task_id}/dataset/{dataset_id}/update', description='update single data')
def dataset_update(task_id: str, dataset_id: str, body):
    pass


@router.delete('/{task_id}/dataset/{dataset_id}/delete', description='delete single data')
def dataset_delete(task_id: str, dataset_id):
    pass


@router.post('/{task_id}/dataset/upload', description='upload and overwrite dataset')
def dataset_upload(task_id: str, body):
    pass


@router.get('/{task_id}/dataset/download', description='download dataset')
def dataset_download(task_id: str):
    pass
