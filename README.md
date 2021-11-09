# Audience API v 2.0

###### created by Weber Huang at 2021-10-07

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
+ [Error code](#error-code)


## Description

此 WEB API 專案是基於協助 RD2 進行貼標任務而建立，支援使用者選擇貼標模型與規則，並且可以呼叫 API 回傳抽象結果。

貼標專案大體流程為，從使用者定義之情況建立貼標任務 (如 日期資訊、資料庫資訊等) ，訪問資料庫擷取相關資料進行貼標，貼標完資料根據來源ID分別儲存至不同的結果資料表。過程的任務資訊 (如 任務開始時間、任務狀態、貼標時間) 和驗證資訊 (如 接收資料、產出資料、上架資料筆數、貼標率) 會儲存於使用者預先定義的結果資料庫中的 state 資料表。

使用者可以透過`tasks_list`, `check_status`, `sample_result`等 API 查詢任務狀態和取得抽樣貼標完結果，或是透過任務ID直接查詢 state 資料表來來取得相關資訊。

These APIs is built for the usage of RD2 data labeling tasks supporting users selecting models and rules to labeling the target range of data, and result sampling. 

The total flow in brief of `create_task` is that the API will query the database via conditions and information which place by users, label those data, and output the data to a target database storing by `source_id` . The progress and validation information will be stored in the table, name `state`, inside the user define output schema which will be automatically created at the first time that user call `create_task` API.

Users can track the progress and result sampling data by calling the rest of APIs `tasks_list`, `check_status`, and `sample_result` or directly query the table `state` by giving the `task_id` information to gain such information.



## Work Flow

<img src="workflow.png">

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

此專案預設使用者已經有初步了解如何使用 Docker。若不清楚使用方法，可以參考 [Docker Guides](https://docs.docker.com/get-started/) 。

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

> Noted that if you only want to specify a single task, add the task name after it in the command, like celery_worker.label_data While in this project it is not suggested since we use the celery canvas to design the total work flow. Users don't have to edit any celery command manually.

`-l` means loglevel; `-P` have to be setup as `solo` in the windows environment. About other pool configurations, see [workers](https://docs.celeryproject.org/en/stable/userguide/workers.html) , [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) ; `-n` represents the worker name; `-Q` means queue name, see official document [workers](https://docs.celeryproject.org/en/stable/userguide/workers.html) for more in depth explanations.

> See [windows issue](https://stackoverflow.com/a/27358974/16810727),  [for command line interface](https://docs.celeryproject.org/en/latest/reference/cli.html) to gain more information. Windows 10 only support -P solo, while solo pool taking each task as a core process (you can only pass another task if one is done), it isn't always being recommended, since it doesn't not support remote control ([see docs](https://docs.celeryproject.org/en/stable/userguide/workers.html#remote-control)) and it can sometimes blocking your task flow.

**Ubuntu**

```bash
# if you wanna run the task with coroutine
# make sure installing the gevent before, `pip install gevent`
$ celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P gevent --concurrency=500

# or run it with threads
$ celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P threads
```

According to [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) , <u>it is suggested to configure the worker with **coroutine**</u> <u>(-P gevent or eventlet) used as I/O bound task like HTTP restfulAPI</u> :

> Let’s say you need to execute thousands of HTTP GET requests to fetch data from external REST APIs. The time it takes to complete a single GET request depends almost entirely on the time it takes the server to handle that request. Most of the time, your tasks wait for the server to send the response, not using any CPU.

#### Run the API

Configure the API address in `settings.py`, default address is localhost

```bash
$ python label_api.py
```



## Usage

If you have done the quick start and you want to test the API functions or expect a web-based user-interface, you can type `<api address>:<api port>/docs` in the browser (for example http://127.0.0.1:8000/docs) to open a Open API user-interface. It is very simple that you just have to choose `try it out` in top-right bottom of each API and replace the request body or query parameter to execute it.

<img src="OpenAPI.png">

Otherwise modify following parts via curl to calling API:

+ `/api/tasks` POST (create_task) :  Input the task information for example model type, predict type, date info, etc., and return task_id with task configuration.

  **input example (default) :**

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

  + Replace your own API address with port
  + For each configuration in request body (feel free to edit them to fit your task): 
    + model_type: labeling model, default is keyword_model
    + predict_type: predicting target, default is author_name
    + start_time and end_time : the query date range
    + target_schema : the target schema where the data you want to label from
    + target_table : the target table under the target schema, where the data you want to label from
    + output_schema : where you want to store the output result
    + countdown : the countdown second between label task and generate_production task
  + Noted that the default values of database are generated from the environment variables from `.env`

  **output example :**

  ```json
  {
      "model_type":"keyword_model",
       "predict_type":"author",
       "start_time":"2020-0101T00:00:00",
       "end_time":"20210101T00:00:00",
       "target_schema":"wh_fb_pm",
       "target_table":"ts_page_content",
       "output_schema":"audience_result",
       "queue":"queue1",
       "countdown":5,
       "date_range":"2020-01-01 00:00:00 - 2021-01-01 00:00:00",
       "task_id":"3a5c4e72410611ecb688d45d6456a14d"
  }
  ```

  Save the `task_id` if you want to directly query the task status or result after.

  

+ `/api/tasks` GET (task_list) : Return the recent created tasks' id and tasks' information (task configuration with result if it was finished).

  **input example :**

  ```shell
  curl -X 'GET' \
    'http://127.0.0.1:8000/api/tasks/' \
    -H 'accept: application/json'
  ```

  **output example :**

  ```json
  {
    "988b791b32d911eca68704ea56825bad": {
      "status": "SUCCESS",
      "model_type": "keyword_model",
      "predict_type": "author_name",
      "date_range": "2018-01-01 00:00:00 - 2018-12-31 23:59:59",
      "target_table": "ts_page_content",
      "create_time": "2021-10-22T09:44:29",
      "result": "forum,Dcard"
    },
    "b773c786320c11eca0ca04ea56825bad": {
      "status": "SUCCESS",
      "model_type": "keyword_model",
      "predict_type": "author_name",
      "date_range": "2018-01-01 00:00:00 - 2018-12-31 23:59:59",
      "target_table": "ts_page_content",
      "create_time": "2021-10-21T09:17:54",
      "result": "wh_panel_mapping_Dcard,wh_panel_mapping_forum"
    },
    "509f463f318611ecbb6a04ea56825bad": {
      "status": "SUCCESS",
      "model_type": "keyword_model",
      "predict_type": "author_name",
      "date_range": "2018-01-01 00:00:00 - 2018-12-31 23:59:59",
      "target_table": "ts_page_content",
      "create_time": "2021-10-20T17:15:49",
      "result": "wh_panel_mapping_forum,wh_panel_mapping_Dcard"
    },
    "0ecd3774318611ec9ecd04ea56825bad": {
      "status": "PENDING",
      "model_type": "keyword_model",
      "predict_type": "author_name",
      "date_range": "2018-01-01 00:00:00 - 2018-12-31 23:59:59",
      "target_table": "ts_page_content",
      "create_time": "2021-10-20T17:13:58",
      "result": ""
    },
    "d135e614317c11ec9f9c04ea56825bad": {
      "status": "SUCCESS",
      "model_type": "keyword_model",
      "predict_type": "author_name",
      "date_range": "2018-01-01 00:00:00 - 2018-12-31 23:59:59",
      "target_table": "ts_page_content",
      "create_time": "2021-10-20T16:07:50",
      "result": "wh_panel_mapping_forum,wh_panel_mapping_Dcard"
    }
  }
  ```

  

+ `/api/tasks/{task_id}` GET (check_status) : Return the task status (*PENDING, SUCCESS, FAILURE*) via task id, if the task is *SUCCESS* return result too.

  **input example :**

  ```shell
  curl -X 'GET' \
    'http://127.0.0.1:8000/api/tasks/b773c786320c11eca0ca04ea56825bad' \
    -H 'accept: application/json'
  ```

  **output example :**

  ````json
  {
    "SUCCESS": "wh_panel_mapping_Dcard,wh_panel_mapping_forum"
  }
  ````

  

+ `/api/tasks/{task_id}/sample/` GET (sample_result) : Input task id and result (table_name), return the sampling results from result tables.

  **input example :**

  ```shell
  curl -X 'GET' \
    'http://127.0.0.1:8000/api/tasks/988b791b32d911eca68704ea56825bad/sample/?table_name=wh_panel_mapping_Dcard&table_name=wh_panel_mapping_forum' \
    -H 'accept: application/json'
  ```

  **output example :**

  ````json
  [
    {
      "id": "1514778057509_F02",
      "task_id": "988b791b32d911eca68704ea56825bad",
      "source_author": "WH_F0116_女神 雅典娜warmman07/M",
      "panel": "/female",
      "create_time": "2018-01-01T11:27:30",
      "field_content": "WH_F0116",
      "match_content": "女神 雅典娜warmman07/M"
    },
    {
      "id": "1514793390003_F02",
      "task_id": "988b791b32d911eca68704ea56825bad",
      "source_author": "WH_F0116_偶4克萊爾爾爾🙈iamclaire926/F",
      "panel": "/female",
      "create_time": "2018-01-01T15:41:48",
      "field_content": "WH_F0116",
      "match_content": "偶4克萊爾爾爾🙈iamclaire926/F"
    },
    {
      "id": "1514795231214_F02",
      "task_id": "988b791b32d911eca68704ea56825bad",
      "source_author": "WH_F0116_生者akaii/M",
      "panel": "/male",
      "create_time": "2018-01-01T16:12:39",
      "field_content": "WH_F0116",
      "match_content": "生者akaii/M"
    },
    {
      "id": "1514799613632_F02",
      "task_id": "988b791b32d911eca68704ea56825bad",
      "source_author": "WH_F0116_馬偕妹ㄓcatherine900117/F",
      "panel": "/female",
      "create_time": "2018-01-01T17:33:31",
      "field_content": "WH_F0116",
      "match_content": "馬偕妹ㄓcatherine900117/F"
    },
    {
      "id": "1514813950284_1_F02",
      "task_id": "988b791b32d911eca68704ea56825bad",
      "source_author": "WH_F0116_思考未來的女子rin00467/F",
      "panel": "/female",
      "create_time": "2018-01-01T21:18:52",
      "field_content": "WH_F0116",
      "match_content": "思考未來的女子rin00467/F"
    },
    {
      "id": "1514829464318_F02",
      "task_id": "988b791b32d911eca68704ea56825bad",
      "source_author": "WH_F0116_Amy Tsais6013104/F",
      "panel": "/female",
      "create_time": "2018-01-02T01:52:34",
      "field_content": "WH_F0116",
      "match_content": "Amy Tsais6013104/F"
    }
  ]
  ````

  | Column        | Description                            |
  | ------------- | -------------------------------------- |
  | id            | Row id from original data              |
  | task_id       | Labeling task id                       |
  | source_author | Combine the s_id with author_name      |
  | panel         | Result of labeling                     |
  | create_time   | Post_time                              |
  | field_content | s_id                                   |
  | match_content | The content which is used to labeling. |

  

## Error code

| Error code | Error message         | Note                                                         |
| ---------- | --------------------- | ------------------------------------------------------------ |
| 200        | OK                    | Successful response                                          |
| 400        | Bad request           | Probably wrong format of API input                           |
| 404        | Not found             | Task id is not exist                                         |
| 500        | Internal Server Error | Probably due to the database or worker problem or server die |


## System Requirement

Testing system information : 

System : Windows 10

Processor : Intel(R) Core(TM) i5-8259U

RAM : 16G

Baseline Performance

+ Data size : 2,376,186 rows
+ Predict model : keyword_base model  
+ Finished time : 23.26 minutes  

+ Max memory usage :   201.80 Mb

