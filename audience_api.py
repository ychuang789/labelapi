import uvicorn
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apis import modeling_api, predicting_api
from utils.general_helper import get_logger, get_config

configuration = get_config()
_logger = get_logger('label_API')
description = """
A backend API which support labeling, modeling and predicting jobs of django site for Audience.          

#### Tools   

##### Task     

1. create_task : a post api which create a labeling task via the information in the request body.    
2. task_list : return the recent tasks and tasks information.     
3. check_status : return a single task status and results if success via task_id.   
4. sample_result : return the labeling results from database via task_id and table information.    
5. abort_task : break a task with a target task_id.    
6. dump_tasks : dump tasks to ZIP.   

##### Model   
 
1. model_preparing : train and validate a model with saving it to model directory, if the model cannot be trained, save the record to model_status.      
2. model_testing : test a model with a external test data.         
3. model_status : get the model status information with a target job_id.       
4. model_report : get the model report information with a target job_id.   
5. model_abort : break a task with a target job_id.   
6. model_delete : delete a record in model_status, it will also wipe out the report in model_report with same task_id.  
7. model_import : input term weight file to a task.
8. get_import_model_status : track the schedule of model_import.
9. get_eval_details :  return a limit query set of detail row data from a specific report of a task.
10. get_eval_false_prediction : return a limit query set of detail false prediction row data from a specific report of a task.
11. get_eval_true_prediction : return a limit query set of detail true prediction row data from a specific report of a task.
12. download_details : download details prediction row data as a csv file of a specific dataset type.
13. term_weight_add : add a single row of term weight to a task.
14. get term weight : retrieve all term weight data from a task.
15. term_weight_update : update a specific term weight data from a task.
16. term_weight_delete : delete a specific term weight data from a task.
17. term_weight_download: download whole term weight data as csv from a task. 

"""

app = FastAPI(title=configuration.API_TITLE,
              description=description,
              version=configuration.API_VERSION,
              # dependencies=[Depends(get_query_token)]
              )


def request_validation_exception_handler(request, exc: RequestValidationError) -> JSONResponse:
    """ref: https://blog.csdn.net/weixin_36179862/article/details/110507491"""

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors())},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

app.include_router(predicting_api.router)
app.include_router(modeling_api.router)

if __name__ == '__main__':
    uvicorn.run("__main__:app", host=configuration.API_HOST, debug=True)
