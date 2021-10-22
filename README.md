# Audience API v 2.0

###### created by Weber Huang at 2021-10-07

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

This API is built for the usage of RD2 data labeling tasks supporting users selecting model and rule  to labeling the target range of data, and result sampling. 



## Work Flow

<img src="workflow.png">

## Built With

Windows 10

Python 3.8

Celery 5.1.2

FastAPI 0.68.1

SQLModel 0.04

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

```bash
$ cd <your project dir>
$ pip install virtualenv

# Setup virtual environment
$ virtualenv venv

# Activate environment
$ venv\Scripts\activate
```

Install packages

```bash
$ pip install -r requirements.txt
```

#### Set up database information

Set the environment variable in your project root directory. Use text editor to create a file with some important info inside:

```bash
HOST=<database host>
PORT=<database port>
USER=<database username>
PASSWORD=<database password>
INPUT_SCHEMA=<database schema where you want to label>
OUTPUT_SCHEMA=<database schema where you want to store the result and state>
```

Replace the value from your own, and save the file as `.env`

#### Initialize the worker

###### Run the worker

Make sure the redis is running beforehand or you should fail to initialize celery

```
$ celery -A celery_worker worker -l INFO -P solo


 -------------- celery@nuc373 v5.1.2 (sun-harmonics)
--- ***** -----
-- ******* ---- Windows-10-10.0.19042-SP0 2021-10-07 13:46:16
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         __main__:0x27ed0212580
- ** ---------- .> transport:   redis://localhost:6379//
- ** ---------- .> results:     redis://localhost/0
- *** --- * --- .> concurrency: 8 (solo)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery


[tasks]
  . celery_worker.label_data


[2021-10-07 13:46:44,686: INFO/MainProcess] Connected to redis://localhost:6379//
[2021-10-07 13:46:44,718: INFO/MainProcess] mingle: searching for neighbors
[2021-10-07 13:46:45,797: INFO/MainProcess] mingle: all alone
[2021-10-07 13:46:45,838: INFO/MainProcess] celery@nuc373 ready.

```

#### Run the API

```bash
$ python label_api.py

INFO:     Started server process [16116]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```



## Usage

Open the link http://127.0.0.1:8000/docs after you run the API to use the APIs at OpenAPI user interface. You can use it by `try it out` to modify the APIs input / output :

<img src="OpenAPI.png">

Or modify following parts: 

+ `/api/tasks` POST (create_task) :  Input the task information for example model type, predict type, date info, etc., and return task_id with task configuration.

  **input example (default) :**

  ```shell
  curl -X 'POST' \
    'http://127.0.0.1:8000/api/tasks/' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "model_type": "keyword_model",
    "predict_type": "author_name",
    "start_time": "2018-01-01 00:00:00",
    "end_time": "2018-12-31 23:59:59",
    "target_schema": "forum_data",
    "target_table": "ts_page_content",
    "date_info": false,
    "batch_size": 1000000
  }'
  ```

  + Edit `model_type`, `predict_type` to select the model and pattern :
    + model_type: keyword_model, rule_model
    + predict_type: author_name, content, s_area_id
  + Edit `start_time`, `end_time`, `target_schema` and `target_table` to select then range of target data you want to labeling: 
    + start_time and end_time refer to the post_time of the data, set `date_info` to *false* if you want to label whole data in table.
    + target_schema and target_table point to which table of data you want to labeling
    + It is suggested to run the task by batch to reduce the usage of memory, `batch_size` means the number of rows you want to execute in each batch (*default* is 1000000)

  **output example :**

  ```json
  {
    "task_id": "7bc4d57a330611ec8fe704ea56825bad",
    "model_type": "keyword_model",
    "predict_type": "author",
    "date_range": "2018-01-01 00:00:00 - 2018-12-31 23:59:59",
    "target_schema": "forum_data",
    "target_table": "ts_page_content",
    "date_info": false,
    "batch_size": 1000000,
    "date_info_dict": {
      "start_time": "2018-01-01T00:00:00",
      "end_time": "2018-12-31T23:59:59"
    }
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

  

