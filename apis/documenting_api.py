from fastapi import APIRouter

from fastapi import status
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse


from apis.input_class.documenting_input import DocumentRequest

router = APIRouter(prefix='/documents',
                   tags=['documents'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )


@router.post('/add', description='add a document task')
def document_add(body: DocumentRequest):
    try:
        # todo: write data into database
        return JSONResponse(status_code=status.HTTP_200_OK, content='OK')
    except Exception as e:
        err_msg = f'failed to add task since {e}'
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))


@router.get('/{task_id}', description='retrieve a task')
def document_retrieve(task_id: str):
    pass


@router.patch('/{task_id}/update', description='update a task')
def document_update(task_id: str, body: DocumentRequest):
    """https://fastapi.tiangolo.com/tutorial/body-updates/#using-pydantics-exclude_unset-parameter"""

    stored_data = body.dict()
    stored_model = DocumentRequest(**stored_data)
    update_data = body.dict(exclude_unset=True)
    updated_data = stored_model.copy(update=update_data)
    # Todo: partial update the data through CRUD class
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
