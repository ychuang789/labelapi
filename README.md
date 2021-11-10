# Audience API v 2.1

###### v2.0 created by Weber Huang at 2021-10-07; v2.1 updated by Weber Huang at 2021-11-09 

#### Table of content

+ [Description](#description)
+ [Work Flow](#work-flow)
+ [Built With](#built-with)
+ [Quick Start](#quick-start)
  + [Set up docker](#set-up-docker)
  + [Set up environment](#set-up-environment)
  + [Set up database information](#set-up-database-information)
  + [Initialize the worker](#initialize-the-worker)
  + [Run the API](#run-the-api)
+ [Usage](#usage)
  + [create_task](#create_task)
  + [task_list](#task_list)
  + [check_status](#check_status)
  + [sample_result](#sample_result)
+ [Error code](#error-code)
+ [System Recommendation and Baseline Performance](#system-recommendation-and-baseline-performance)



## Description

此 WEB API 專案基於協助 RD2 站台進行貼標任務而建立，支援使用者選擇貼標模型與規則，並且可以呼叫 API 回傳抽樣結果檢查貼概況。此專案共有四個 API 服務:

1. create_task : 依據使用者定義之情況，建立任務流程 (貼標 -> 上架)，並執行任務
2. task_list : 回傳近期執行之任務與之相關資訊
3. check_status : 輸入任務ID，檢查任務進度與任務結果(資料表名稱)
4. sample_result : 輸入任務ID與結果資料表名稱，回傳抽樣之上架資料

貼標專案流程為，從使用者定義之情況建立貼標任務 (如 日期資訊、資料庫資訊等) ，訪問資料庫擷取相關資料進行貼標，貼標完資料根據來源分別儲存至不同的結果資料表。過程的任務資訊 (如 任務開始時間、任務狀態、貼標時間) 和驗證資訊 (如 接收資料長度、產出資料長度、上架資料筆數、貼標率等) 會儲存於使用者預先定義的結果資料庫中的 state 資料表。最後使用者可以透過

使用者可以透過`tasks_list`, `check_status`, `sample_result`等 API 查詢任務狀態和取得抽樣貼標完結果，或是透過任務ID直接查詢 state 資料表來來取得相關資訊。

---

These WEB APIs is built for the usage of RD2 data labeling tasks supporting users selecting models and rules to labeling the target range of data, and result sampling. There are four API in this project:

1. create_task : According to the user defined condition, set up a task flow (labeling and generate production) and execute the flow
2. task_list : return the recent executed tasks with tasks' information
3. check_status : Input a task id to check the status and result (result table name) of the task
4. sample_result : Input a task id with result table name, return a sampling dataset back.

The total flow in brief of `create_task` is that the API will query the database via conditions and information which place by users, label those data, and output the data to a target database storing by `source_id` . The progress and validation information will be stored in the table, name `state`, inside the user define output schema which will be automatically created at the first time that user call `create_task` API.

Users can track the progress and result sampling data by calling the rest of APIs `tasks_list`, `check_status`, and `sample_result` or directly query the table `state` by giving the `task_id` information to gain such information.



## Work Flow

<img src="workflow_chain.PNG">

## Built With

+ Develop with following tools
  + Windows 10
  + Docker
  + Redis
  + MariaDB
  + Python 3.8
  + Celery 5.1.2
  + FastAPI 0.68.1
+ Test with
  + Windows 10 Python 3.8
  
  + Ubuntu 18.04.5 LTS Python 3.8
  
    

## Quick Start

#### Set up docker

If you are already using docker, skip this part.

Before starting this project, we assume users have downloaded docker. About how to use docker, users may refer to [Docker Guides](https://docs.docker.com/get-started/).

#### Set up environment

Download docker version of *Redis* beforehand

```bash
$ docker run -d -p 6379:6379 redis
```

Get into the virtual environment

**Windows**

```bash
# clone the project
$ git clone -b 14-optimize-audience-task-flow --single-branch https://ychuang:weber1812eland@gitting.eland.com.tw/rd2/audience/audience-api.git

# get into the project folder
$ cd <your project dir>

# Setup virtual environment
# Require the python virtualenv package, or you can setup the environment by other tools 
$ virtualenv venv

# Activate environment
# Windows
$ venv\Scripts\activate

# Install packages
$ pip install -r requirements.txt
```

**Ubuntu**

```bash
# clone the project
$ git clone -b 14-optimize-audience-task-flow --single-branch https://ychuang:weber1812eland@gitting.eland.com.tw/rd2/audience/audience-api.git\

# get into the project folder
$ cd <your project dir>

# set up the environment
$ bash setup.sh
```

#### Set up database information

Set the database environment variables information in your project root directory. Create a file, name `.env` , with some important info inside:

```bash
INPUT_HOST=<database host which you want to label>
INPUT_PORT=<database port which you want to label>
INPUT_USER=<database user info which you want to label>
INPUT_PASSWORD=<database password which you want to label>
INPUT_SCHEMA=<database schema where you want to label>
OUTPUT_HOST=<database host where you want to save output>
OUTPUT_PORT=<database port where you want to save output>
OUTPUT_USER=<database user info where you want to save output>
OUTPUT_PASSWORD=<database password where you want to save output>
OUTPUT_SCHEMA=<database schema where you want to save output>
```

#### Initialize the worker

###### Run the worker

Make sure the redis is running beforehand or you should fail to initialize celery.

Before running the celery worker, edit the `CeleryConfig` in `settings.py` to specify the broker and backend, see [Backends and Brokers](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html) for more details configuration.

**Windows**

```bash
$ celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P solo
```

`-l` means loglevel; `-P` have to be setup as `solo` in the windows environment. About other pool configurations, see [workers](https://docs.celeryproject.org/en/stable/userguide/workers.html) , [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) ; `-n` represents the worker name; `-Q` means queue name, see official document [workers](https://docs.celeryproject.org/en/stable/userguide/workers.html) for more in depth explanations. 

> Noted that if you only want to specify a single task, add the task name after it in the command, like `celery_worker.label_data` While in this project it is not suggested since we use the celery canvas to design the total work flow. Users **DON'T** have to edit any celery command manually.

> See [windows issue](https://stackoverflow.com/a/27358974/16810727),  [for command line interface](https://docs.celeryproject.org/en/latest/reference/cli.html) to gain more information. Windows 10 only support `-P solo`, while solo pool taking each task as a core process (you can only pass another task if one is done), `-P solo` isn't always being recommended, since it doesn't not support remote control ([see docs](https://docs.celeryproject.org/en/stable/userguide/workers.html#remote-control)) and it can sometimes blocking your task flow.

**Ubuntu**

```bash
# if you wanna run the task with coroutine
# make sure installing the gevent before `pip install gevent`
$ celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P gevent --concurrency=500

# or run it with threads
$ celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P threads
```

According to [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) , it is suggested to configure the worker with **coroutine** (`-P gevent` or `-P eventlet`) used as I/O bound task like HTTP restful API :

> Let’s say you need to execute thousands of HTTP GET requests to fetch data from external REST APIs. The time it takes to complete a single GET request depends almost entirely on the time it takes the server to handle that request. Most of the time, your tasks wait for the server to send the response, not using any CPU.

#### Run the API

Configure the API address in `settings.py`, default address is localhost

```bash
$ python label_api.py
```



## Usage

If you have done the quick start and you want to test the API functions or expect a web-based user-interface, you can type `<api address>:<api port>/docs` in the browser (for example http://127.0.0.1:8000/docs) to open a Swagger user-interface, for more information see [Swagger](https://swagger.io/). It is very simple that you just have to choose `try it out` in top-right bottom of each API and replace the request body or query parameter to execute it.

<img src="OpenAPI.PNG">

Otherwise modify following parts via curl to calling API



#### create_task

Input the task information for example model type, predict type, date info, etc., and return task_id with task configuration.

+ **request example :**

```shell
curl -X 'POST' \
  'http://<api address>:<api port>/api/tasks/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model_type": "keyword_model",
  "predict_type": "author_name",
  "start_time": "2020-01-01 00:00:00",
  "end_time": "2021-01-01 00:00:00",
  "target_schema": "wh_fb_pm",
  "target_table": "ts_page_content",
  "output_schema": "audience_result",
  "countdown": 5
}'
```

​	Replace your own API address with port

​	For each configuration in request body (feel free to edit them to fit your task): 

| name                    | description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| model_type              | labeling model, default is keyword_model                     |
| predict_type            | predicting target, default is author_name                    |
| start_time and end_time | the query date range                                         |
| target_schema           | the target schema where the data you want to label from      |
| target_table            | the target table under the target schema, where the data you want to label from |
| output_schema           | where you want to store the output result                    |
| countdown               | the countdown second between label task and generate_production task |

​	Noted that the default values of database are generated from the environment variables from `.env`

+ **response example :**

```json
{
    "error_code":200,
     "error_message":{
         "model_type":"keyword_model",
         "predict_type":"author",
         "start_time":"2020-01-01T00:00:00",
         "end_time":"2021-01-01T00:00:00",
         "target_schema":"wh_fb_ex_02",
         "target_table":"ts_page_content",
         "output_schema":"audience_result",
         "countdown":5,"queue":"queue1",
         "date_range":"2020-01-01 00:00:00 - 2021-01-01 00:00:00",
         "task_id":"8fec5762412c11ec836d04ea56825baa"
 }
}
```

Save the `task_id` if you want to directly query the task status or result after.



#### task_list

Return the recent created tasks' id with some tasks' information.

Request example :

```shell
curl -X 'GET' \
  'http://<api address>:<api port>/api/tasks/' \
  -H 'accept: application/json'
```

Replace your own API address with port

Response example :

```json
{
  "error_code": 200,
  "error_message": "OK",
  "content": [
    {
      "task_id": "8fec5762412c11ec836d04ea56825baa",
      "stat": "PENDING",
      "prod_stat": null,
      "model_type": "keyword_model",
      "predict_type": "author",
      "date_range": "2020-01-01 00:00:00 - 2021-01-01 00:00:00",
      "target_table": "wh_fb_ex_02",
      "create_time": "2021-11-09T15:13:39",
      "peak_memory": null,
      "length_receive_table": null,
      "length_output_table": null,
      "length_prod_table": null,
      "result": "",
      "uniq_source_author": null,
      "rate_of_label": null,
      "run_time": null,
      "check_point": null
    },
    {
      "task_id": "7c7bd38c410a11ecb688d45d6456a14d",
      "stat": "SUCCESS",
      "prod_stat": "finish",
      "model_type": "keyword_model",
      "predict_type": "author",
      "date_range": "2020-01-01 00:00:00 - 2021-01-01 00:00:00",
      "target_table": "wh_fb_ex",
      "create_time": "2021-11-09T11:09:43",
      "peak_memory": null,
      "length_receive_table": 16992036,
      "length_output_table": 2030847,
      "length_prod_table": 236705,
      "result": "fbfans",
      "uniq_source_author": "1672893",
      "rate_of_label": "14.15",
      "run_time": 170.345,
      "check_point": null
    },
    {
      "task_id": "3a5c4e72410611ecb688d45d6456a14d",
      "stat": "SUCCESS",
      "prod_stat": "finish",
      "model_type": "keyword_model",
      "predict_type": "author",
      "date_range": "2020-01-01 00:00:00 - 2021-01-01 00:00:00",
      "target_table": "wh_fb_pm",
      "create_time": "2021-11-09T10:39:14",
      "peak_memory": null,
      "length_receive_table": 92491,
      "length_output_table": 19687,
      "length_prod_table": 10725,
      "result": "fbpm",
      "uniq_source_author": "50216",
      "rate_of_label": "21.36",
      "run_time": 1.63621,
      "check_point": null
    },
      .
      .
      .
  ]
}
```

| name                 | description                                                  |
| -------------------- | ------------------------------------------------------------ |
| task_id              | task id                                                      |
| stat                 | status of labeling task (PENDING, SUCCESS, FAILURE)          |
| prod_stat            | status of generate production task (finish or null)          |
| model_type           | model used by labeling                                       |
| predict_type         | predict target                                               |
| date_range           | users define date range of create_task                       |
| target_table         | target schema which query for labeling                       |
| create_time          | task starting datetime                                       |
| ~~peak_memory~~      | ~~trace the max memory of each labeling task~~ *This function is expired and out of usage in this version* |
| length_receive_table | the number of data from target_table                         |
| length_output_table  | the number of result after labeling                          |
| length_prod_table    | the number of result after generate production               |
| result               | the temp result table of labeling task                       |
| uniq_source_author   | for each task, the unique `source_id` , `author` from their data source (only use for calculating rate_of_label) |
| rate_of_label        | percentage of length of result generated by generate_production divided by uniq_source_author |
| check_point          | if the labeling task is failed, save the batch number (datetime) for last execution |



#### check_status

`/api/tasks/{task_id}` 

Return the task status (*PENDING, SUCCESS, FAILURE*) via task id, if the task is *SUCCESS* return result (temp result table_name) too.

Request example :

```shell
curl -X 'GET' \
  'http://<api address>:<api port>/api/tasks/<task_id>' \
  -H 'accept: application/json'
```

Response example :

````json
{
  "error_code": 200,
  "error_message": "OK",
  "status": "SUCCESS",
  "prod_status": "finish",
  "result": "fbfans"
}
````

| name        | description                                                  |
| ----------- | ------------------------------------------------------------ |
| status      | status of label task                                         |
| prod_status | status of generate production task                           |
| result      | temp result table name of label task in output schema, if generate production is finished the result will be store in `wh_panel_mapping_{result}` in the same output schema |



#### sample_result

`/api/tasks/{task_id}/sample/` 

Input task id and generate_production task's result (table_name from table state with `wh_panel_mapping_` prefix, IF <u>prod_stat</u> is finish), return the sampling results from result tables.

Request example :

```shell
curl -X 'GET' \
  'http://<api address>:<api port>/api/tasks/<task_id>/sample/?table_name=wh_panel_mapping_fbfans' \
  -H 'accept: application/json'
```

Response example :

````json
{
  "error_code": 200,
  "error_message": [
    {
      "id": "1577818324915_FBEXUB",
      "task_id": "7c7bd38c410a11ecb688d45d6456a14d",
      "source_author": "WH_F0045_Kuan Vera",
      "panel": "/female",
      "create_time": "2020-01-01T00:00:03",
      "field_content": "WH_F0045",
      "match_content": "Kuan Vera"
    },
    {
      "id": "1577829993490_FBEXUA",
      "task_id": "7c7bd38c410a11ecb688d45d6456a14d",
      "source_author": "WH_F0045_Tommy T J Tan",
      "panel": "/male",
      "create_time": "2020-01-01T00:00:06",
      "field_content": "WH_F0045",
      "match_content": "Tommy T J Tan"
    },
    {
      "id": "1577830450425_FBEXUA",
      "task_id": "7c7bd38c410a11ecb688d45d6456a14d",
      "source_author": "WH_F0045_Clarice Ooi",
      "panel": "/female",
      "create_time": "2020-01-01T00:00:57",
      "field_content": "WH_F0045",
      "match_content": "Clarice Ooi"
    },
    {
      "id": "1577830451940_FBEXUA",
      "task_id": "7c7bd38c410a11ecb688d45d6456a14d",
      "source_author": "WH_F0045_林超哥",
      "panel": "/male",
      "create_time": "2020-01-01T00:01:15",
      "field_content": "WH_F0045",
      "match_content": "林超哥"
    },
      .
      .
      .
  ]
}
````

| Column        | Description                               |
| ------------- | ----------------------------------------- |
| id            | Row id from original data                 |
| task_id       | Labeling task id                          |
| source_author | Combine the s_id with author_name         |
| panel         | Result of labeling                        |
| create_time   | Post_time                                 |
| field_content | s_id                                      |
| match_content | The content which is matched to labeling. |



## Error code 

+ create_task

  code 200 represent successful

  | error_code | error_message                                                |
  | ---------- | ------------------------------------------------------------ |
  | 200        | task configuration with `task_id`                            |
  | 400        | start_time must be earlier than end_time                     |
  | 500        | failed to start a labeling task, additional error message: <Exception> |
  | 501        | Cannot read pattern file, probably unknown file path or file is not exist, additional error message: <Exception> |
  | 503        | Cannot connect to output schema, additional error message: <Exception> |

+ tasks_list

  code 200 represent successful

  | error_code | error_message                 |
  | ---------- | ----------------------------- |
  | 200        | OK                            |
  | 500        | cannot connect to state table |

+ check_status

  code 200 represent successful

  | error_code | error_message                                                |
  | ---------- | ------------------------------------------------------------ |
  | 200        | OK                                                           |
  | 400        | task id is not exist, plz re-check the task id. Addition error message: <Exception> |

+ sample_result

  code 200 represent successful

  | error_code | error_message                                                |
  | ---------- | ------------------------------------------------------------ |
  | 200        | sampling result                                              |
  | 400        | <task_id> is not in proper format, expect 32 digits get <length of task_id> digits |
  | 404        | empty result, probably wrong combination of task_id and table_name, please check table state or use /api/tasks/<task_id> first |
  | 500        | Cannot scrape data from result tables. Additional error message: <Exception> |

+ error code for Open API

  | Error code | error_message       |
  | ---------- | ------------------- |
  | 200        | Successful Response |
  | 422        | Validation Error    |



## System Recommendation and Baseline Performance

Recommend System : Ubuntu 18.04.5 LTS (Recommended) or Windows 10 (Noted the multiprocessing issue of celery in WIN10 )

Recommend python environment : Python 3.8

Recommend processor : Intel(R) Core(TM) i5-8259U + or other processor with same efficiency

RAM : 16G +

Baseline Performance

+ Data size : 2,376,186 rows
+ Predict model : keyword_base model  
+ Finished time : 23.26 minutes  

+ Max memory usage :   201.80 Mb

