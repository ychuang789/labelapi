import uvicorn
from fastapi import FastAPI

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
"""

app = FastAPI(title=configuration.API_TITLE,
              description=description,
              version=configuration.API_VERSION,
              # dependencies=[Depends(get_query_token)]
              )

app.include_router(predicting_api.router)
app.include_router(modeling_api.router)


if __name__ == '__main__':
    uvicorn.run("__main__:app", host=configuration.API_HOST, debug=True)
