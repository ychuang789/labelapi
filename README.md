# Audience API v 2.2

###### v2.0 created by Weber Huang at 2021-10-07; v2.2 last updated by Weber Huang at 2022-02-23

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
  + [Swagger](#swagger)
  + [Example](#eample)
+ [Error code](#error-code)
+ [System Recommendation and Baseline Performance](#system-recommendation-and-baseline-performance)
+ [Appendix](#appendix)

## Description

Audience API is built for the usage of data labeling ETL pipeline supporting users selecting models and rules to label the target range of data, and result sampling. There are several APIs in this project:

+ **documenting**
  + Users can access [**doccano**](https://rd2demo.eland.com.tw/), a models' data annotation platform which supporting data annotation.
  + Allow users to upload the annotated models' data, for example, machine learning and rule datasets.
  + Users can perform the CRUD of data management.
+ **modeling**
  + Apply the dataset which is managed by documenting API to train, validate and test the model.
  + Support the table of classification report and the download link of validation details.

+ **predicting**
  + Users can choose several models and source databases, choose the time range, to start the predicting ETL pipeline.
  + While running the task, users can determine if the task shall keep running or stop the task by viewing the sampling result.
  + Users can check the task status to gain the task information, such as the progression, statistics data and error message, etc.

+ **preprocessing**
  + Define sets of regular expression data that can be excluded before the model training or predicting ETL.
  + Noted this API is not available for the users yet. 

## Work Flow

#### Modeling API

![](C:\Users\ychuang\PycharmProjects\Audience_api\graph\Audience-modeling_pipline.drawio (2).png)

#### Predicting API

![](C:\Users\ychuang\PycharmProjects\Audience_api\graph\Audience-Predicting_flow.drawio (1).png)



## Built With

+ Develop with following tools
  + Windows 10
  + Docker
  + Redis
  + MariaDB
  + Python 3.8
  + Celery 5.1.2
  + FastAPI 0.68.1
  + Scikit-learn
  + Sqlalchemy
+ Deploy with
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
$ git clone https://ychuang:weber1812eland@gitting.eland.com.tw/rd2/audience/audience-api.git

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
$ git clone https://ychuang:weber1812eland@gitting.eland.com.tw/rd2/audience/audience-api.git

# get into the project folder
$ cd <your project dir>

# set up the environment
$ virtualenv venv -p $(which python3.8)

# get in environment
$ source venv/bin/activate

# check the interpreter
$ which python

# install packages
$ pip install -r requirements.txt
```

> You can use `tmux` to build a background session in Linux system to deploy the celery worker, see [tmux shortcuts & cheatsheet](https://gist.github.com/MohamedAlaa/2961058), [Getting started with Tmux](https://linuxize.com/post/getting-started-with-tmux/) or [linux tmux terminal multiplexer tutorial](https://blog.gtwang.org/linux/linux-tmux-terminal-multiplexer-tutorial/) to gain more information.

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
ENV=<choose between `development` or `production`>
```

> For ENV, development is set default as localhost (127.0.0.1) while you can edit the`ProductionConfig` in `settings.py` 

#### Initialize the worker

###### Run the worker

Make sure the redis is running beforehand or you should fail to initialize celery.

**Windows**

+ Task

```bash
$ make run_predicting_1
# $ make run_predicting_2
```

+ Model

```bash
$ make run_modeling_1
```

We use `gevent` to run a worker, see `Makefile` for more information.

For detailed option command of celery, `-l` means loglevel; `-P` **CANNOT** be set as default, namely `prefork`, in the windows environment. About other pool configurations, see [workers](https://docs.celeryproject.org/en/stable/userguide/workers.html) , [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) ; `-n` represents the worker name; `-Q` means queue name, see official document [workers](https://docs.celeryproject.org/en/stable/userguide/workers.html) for more in depth explanations. Noted that in this project we assume the users will only run a single worker and single queue, if you want to run multiple workers or multiple queues, you may add it manually add the second, third, etc.

> Noted that if you only want to specify a single task, add the task name after it in the command, like `celery_worker.label_data` While in this project it is not suggested since we use the celery canvas to design the total work flow. Users **DON'T** have to edit any celery command manually.

> See [windows issue](https://stackoverflow.com/a/27358974/16810727),  [for command line interface](https://docs.celeryproject.org/en/latest/reference/cli.html) to gain more information. Windows 10 don't support  default pool config `-P prefork`, but it support `-P solo`, `gevent` and `evenlet`, etc. While solo pool taking each task as a core process (you can only pass another task if one is done), `-P solo` isn't always being recommended, since it doesn't allow remote control ([see docs](https://docs.celeryproject.org/en/stable/userguide/workers.html#remote-control)).

**Ubuntu**

+ Task

```bash
$ make run_predicting_1
# $ make run_predicting_2
```

+ Model

```bash
$ make run_modeling
```

According to [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) , it is suggested to configure the worker with **coroutine** (`-P gevent` or `-P eventlet`) used as I/O bound task like HTTP restful API :

> Let’s say you need to execute thousands of HTTP GET requests to fetch data from external REST APIs. The time it takes to complete a single GET request depends almost entirely on the time it takes the server to handle that request. Most of the time, your tasks wait for the server to send the response, not using any CPU.

#### Run the API

Configure the API address in `settings.py`, default address is localhost with port 8000

```bash
$ make run_api
```

## Usage

If you have done the quick start and you want to test the API functions or expect a web-based user-interface, you can type `<api address>:<api port>/docs` in the browser (for example http://127.0.0.1:8000/docs) to open a Swagger user-interface, for more information see [Swagger](https://swagger.io/). It is very simple to use by following the quick demonstration below :

### Swagger 

+ Type `<api address>:<api port>/docs` in the web browser, for example if you test the API at localhost `127.0.0.1/docs`

<img src="graph/OpenAPI.PNG">

+ Open the API you want to test: 

<img src="graph/s1_d.png">

+ Edit the information

<img src="graph/s2_d.png">

+ View the result

<img src="graph/s3_d.png">



## Error code 

Error code in this project is group by <u>API task error code</u> and <u>HTTP error code</u> : 

**API task error code**

+ create_task

  code 200 represent success

  | error_code | error_message                                                |
  | ---------- | ------------------------------------------------------------ |
  | 200        | task configuration with `task_id`                            |
  | 400        | start_time must be earlier than end_time                     |
  | 500        | failed to start a labeling task, additional error message: <Exception> |
  | ~~501~~    | ~~cannot read pattern file, probably unknown file path or file is not exist, additional error message: <Exception>~~ |
  | 503        | cannot connect to output schema, additional error message: <Exception> |

+ tasks_list

  code 200 represent success

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

  code 200 represent success

  | error_code | error_message                                                |
  | ---------- | ------------------------------------------------------------ |
  | 200        | sampling result                                              |
  | 400        | <task_id> is not in proper format, expect 32 digits get <length of task_id> digits |
  | 404        | result table is not found, plz wait for awhile to retry it   |
  | 500        | cannot scrape data from result tables. Additional error message: <Exception> |

  > 404 : since we execute labeling by batch, there will be no result_table information if there is still no batch data write into the output table, so please wait.

+ abort_result

  code 200 represent success

  | error_code | error_message                                                |
  | ---------- | ------------------------------------------------------------ |
  | 200        | successfully send break status to task <task_id> in state    |
  | 400        | <task_id> is not in proper format, expect 32 digits get <length of task_id> digits |
  | 500        | failed to send break status to task,. Additional error message: <Exception> |

**HTTP error code**

| Error code | error_message         | description                                                  |
| ---------- | --------------------- | ------------------------------------------------------------ |
| 200        | Successful Response   | API successfully receive the required information            |
| 400        | Bad Request           |                                                              |
| 404        | Not Found             |                                                              |
| 422        | Validation Error      | API doesn't receive the proper information. This problem usually occurs in <u>wrong format of request body</u> at users post a create_task API |
| 500        | Internal Server Error |                                                              |

# Test

There are two type of test file in this project, api and the rest. All of the testing files are managed under the tests directory, below is the test file structure:

```
tests
├── __init__.py
├── api
│   ├── __init__.py
│   ├── test_modeling_api.py
│   └── test_predicting_api.py
├── connection
│   ├── __init__.py
│   └── test_connection.py
├── model
│   ├── __init__.py
│   ├── test_model_creator.py
│   ├── test_rulebase_models.py
│   └── test_supervise_models.py
├── sample_data
│   ├── dev.csv
│   ├── labels.json
│   ├── rulebase_testdata.csv
│   ├── test.csv
│   └── train.csv
└── worker
    ├── __init__.py
    ├── test_dump_worker.py
    ├── test_modeling_worker.py
    ├── test_orm_worker.py
    └── test_predict_worker.py

```

For API testing, please run the command:

```shell
$ make test_api
```

> Notice that this will test both modeling_api and predicting_api, if you want to test them one-by-one, please use `pytest <file dir>`

For the rest of the parts:

```shell
$ python test.py --help
Usage: test.py [OPTIONS]

Options:
  -D, --dir TEXT     [required]
  -F, --file TEXT    [required]
  -C, --class_ TEXT
  -M, --method TEXT
  --help             Show this message and exit.
```

for example:

```shell
$ python test.py -D worker -F test_modeling_worker -C TestModelingWorker2

test tests.worker.test_modeling_worker.TestModelingWorker2
[2022-01-12 10:22:43,572][modeling][INFO] start eval_outer_test_data task: 3298be1f6def11eca8ca04ea56825bad
[2022-01-12 10:22:43,572][modeling][INFO] Initializing the model term_weight_model...
[2022-01-12 10:22:43,580][modeling][INFO] preparing the datasets for task: 3298be1f6def11eca8ca04ea56825bad
[2022-01-12 10:22:44,024][modeling][INFO] load the model 0_term_weight_model ...
[2022-01-12 10:22:44,025][modeling][INFO] evaluating with ext_test data ...
[2022-01-12 10:22:44,186][modeling][INFO] modeling task: 3298be1f6def11eca8ca04ea56825bad is finished
.
----------------------------------------------------------------------
Ran 1 test in 0.692s

OK
```



## System Recommendation and Baseline Performance

**System Recommendation**

+ System : Ubuntu 18.04.5 LTS (Recommended) or Windows 10 (Noted the multiprocessing issue of celery in WIN10 )
+ Python environment : Python 3.8

+ Processor : Intel(R) Core(TM) i5-8259U + or other processor with same efficiency

+ RAM : 16G +

**Baseline Performance**

+ Data size : 39,291,336 row
+ Predict model : keyword_base model  
+ Finished time : 149.378 minutes  
+ Max memory usage(maximum resident set size ) :   812.38 Mb



## Appendix

**1. Problem of celery multiprocessing (Unsolved)**

```bash
[2021-11-09 09:03:32,151: ERROR/ForkPoolWorker-7] Task celery_worker.label_data[db5f76cc40f811ecb688d45d6456a14d] raised unexpected: AssertionError('daemonic processes are not allowed to have children')
Traceback (most recent call last):
  File "/home/deeprd2/audience-api/venv/lib/python3.8/site-packages/celery/app/trace.py", line 450, in trace_task
    R = retval = fun(*args, **kwargs)
  File "/home/deeprd2/audience-api/venv/lib/python3.8/site-packages/celery/app/trace.py", line 731, in __protected_call__
    return self.run(*args, **kwargs)
  File "/home/deeprd2/audience-api/utils/worker_core.py", line 15, in measure_task
    mem_usage, result = memory_usage(
  File "/home/deeprd2/audience-api/venv/lib/python3.8/site-packages/memory_profiler.py", line 330, in memory_usage
    p.start()
  File "/usr/lib/python3.8/multiprocessing/process.py", line 118, in start
    assert not _current_process._config.get('daemon'), \
AssertionError: daemonic processes are not allowed to have children
```

The problem is due to the memory tracking decorator from `utils/worker_core.py` used by `celery_woker.py` : 

```python
@celery_app.task(name=f'{name}.label_data', track_started=True)
@memory_usage_tracking # this line
def label_data(task_id: str, **kwargs) -> List[str]:
```

It seems that the problem is cause by the python memory tracing module, `memory_profiler`, which uses the build-in python multiprocessing module. While in local environment (windows10) configure the pooling strategy with celery command `-P solo`, it is fine. The problem occurs when deploys the project to remote Linux using multiprocessing default pooling `-P prefork`.

In [Celery Execution Pools: What is it all about?](https://www.distributedpython.com/2018/10/26/celery-execution-pool/) it says : 

> The prefork pool implementation is based on Python’s [multiprocessing](https://docs.python.org/dev/library/multiprocessing.html#module-multiprocessing) package. It allows your Celery worker to side-step [Python’s Global Interpreter Lock](https://docs.python.org/dev/glossary.html#term-global-interpreter-lock) and fully leverage multiple processors on a given machine.

Some cases of similar issues with celery multiprocessing at official Git hub : 

[Tasks are not allowed to start sub processes](https://github.com/celery/celery/issues/1709) 

[daemonic processes are not allowed to have children](https://github.com/celery/celery/issues/4525)

Ok, it seems that the problem is about python multiprocessing module (`-P prefork`), there is nothing wrong currently by switching `-P prefork` to `-P threads` under the ubuntu environment.

So how about using `eventlet` or `gevent`? with a multiprocessing module, they will all fail. I still cannot figure out any clue about this problem, the current way is to disable the memory track decorator, since it is not directly related to the project goal. 



