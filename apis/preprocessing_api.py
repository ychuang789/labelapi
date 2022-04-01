import os
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from apis.input_class.preprocessing_input import PreprocessTaskDelete, PreprocessTaskUpdate
from definition import PREPROCESS_FOLDER
from workers.orm_core.preprocess_operation import PreprocessCRUD
from workers.preprocessing.preprocess_core import PreprocessWorker

router = APIRouter(prefix='/preprocess',
                   tags=['preprocess'],
                   # dependencies=[Depends(get_token_header)],
                   responses={404: {"description": "Not found"}},
                   )


@router.post('/create_task/', description='create preprocess task')
def create_task(name: str = Form(...), feature: str = Form("CONTENT"),
                model_name: str = Form("REGEX_MODEL"), file: UploadFile = File(...)):
    upload_filepath = os.path.join(PREPROCESS_FOLDER, file.filename)
    worker = PreprocessCRUD()
    try:
        with open(upload_filepath, 'wb+') as file_object:
            file_object.write(file.file.read())
        worker.create_task(name, feature, model_name, datetime.now(), upload_filepath)
        err_msg = f"successfully create task"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"failed to create task since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        worker.dispose()


@router.put('/{task_id}/upload_rules', description='upload rules to task')
def upload_rules(task_id, file: UploadFile = File(...)):
    upload_filepath = os.path.join(PREPROCESS_FOLDER, file.filename)
    worker = PreprocessCRUD()
    try:
        with open(upload_filepath, 'wb+') as file_object:
            file_object.write(file.file.read())
        worker.bulk_add_filter_rules(task_pk=task_id, bulk_rules=PreprocessWorker.read_csv_file(upload_filepath))
        err_msg = f"successfully upload rules for task {task_id}"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))

    except Exception as e:
        err_msg = f"failed to upload rules since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=jsonable_encoder(err_msg))
    finally:
        worker.dispose()


@router.delete('/delete_task/', description='delete the task by id')
def delete_task(body: PreprocessTaskDelete):
    worker = PreprocessCRUD()
    try:
        worker.delete_task(task_pk=body.TASK_ID)
        err_msg = f"successfully delete task {body.TASK_ID}"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"failed to delete task {body.TASK_ID} since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        worker.dispose()


@router.post('/{task_id}/update_task', description='update the task information')
def update_task(task_id, body: PreprocessTaskUpdate):
    worker = PreprocessCRUD()
    try:
        worker.update_task(task_pk=task_id, **body.__dict__)
        err_msg = f"successfully update task {task_id}"
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(err_msg))
    except Exception as e:
        err_msg = f"failed to update task {task_id} since {e}"
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=jsonable_encoder(err_msg))
    finally:
        worker.dispose()
