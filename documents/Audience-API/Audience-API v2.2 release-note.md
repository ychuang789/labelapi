##  一、使用工具

+ FastAPI
+ Celery

## 二、開發項目

**1. 新增**

​	**API**

+ abort_task : 支援使用者可以提前從外部中斷正在進行的任務。

​    **Database**

+ 任務資料表 : 新增 error_message 欄位。

​    **Worker**

+ dump_result: 上架任務功能產出上架資料表。

**2. 改良**

​	**API**

+ create_task : 舊版規則與連線寫在內部程式，此版本調整 API request 參數，支援使用者帶入外部規則與資料庫連線資訊。

+ check_status : 舊版僅回傳任務進度狀態，此版本除了能回傳狀態之外支援回傳任務所有資訊，包含開始時間、任務結果統計資訊、錯誤訊息等等。

+ result_sample : 舊版僅支持任務完成抽樣結果，此版本修改抽樣目標由 wh_panel_mapping 至 temp 資料表，因此任務進行中能隨時抽樣貼標結果。

## 三、產品使用說明

#### API

+ create_task:  POST`/tasks/`

  + request example

    pattern: 貼標規則，需對應模型規則輸入格式

    site_config: 信義機房目標資料庫連線資訊

  ```bash
  curl -X 'POST' \
    'http://<api address>:<api port>/api/tasks/' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "MODEL_TYPE": "keyword_model",
    "PREDICT_TYPE": "author_name",
    "START_TIME": "2020-01-01",
    "END_TIME": "2021-01-01",
    "PATTERN": {},
    "INPUT_SCHEMA": "wh_tiktok",
    "INPUT_TABLE": "ts_page_content",
    "OUTPUT_SCHEMA": "audience_result",
    "COUNTDOWN": 5,
    "QUEUE": "queue1",
    "SITE_CONFIG": {"host": <source.host>,
    				 "port": <source.port>,
                   "user": <source.username>,
                   "password": <source.password>,
                   "db": <source.schema>,
                   "charset": "utf8mb4"}
  }'
  
  ```

  + response example

  ```bash
  {
      "error_code":200,
       "error_message":{
           "model_type":"keyword_model",
           "predict_type":"author",
           "start_time":"2020-01-01",
           "end_time":"2021-01-01",
           "target_schema":"wh_fb_ex_02",
           "target_table":"ts_page_content",
           "output_schema":"audience_result",
           "countdown":5,
           "queue":"queue1",
           "date_range":"2020-01-01 - 2021-01-01",
           "task_id":"8fec5762412c11ec836d04ea56825baa"
   }
  }
  
  ```

+ check_status: GET `/tasks/{task_id}`

  + response example

  ```bash
  {
    "error_code": 200,
    "error_message": {
      "task_id": "535b5afb57ed11eca09604ea56825bad",
      "stat": "SUCCESS",
      "prod_stat": "finish",
      "model_type": "rule_model",
      "predict_type": "content",
      "date_range": "2021-01-01 - 2021-03-01",
      "target_table": "wh_bbs_02",
      "create_time": "2021-12-08T14:08:56",
      "peak_memory": null,
      "length_receive_table": 5760849,
      "length_output_table": 536715,
      "length_prod_table": "109614",
      "result": "Ptt",
      "uniq_source_author": "228206",
      "rate_of_label": "48.03",
      "run_time": 33.9207,
      "check_point": null,
      "error_message": null
    }
  }
  
  ```

+ abort_task

  + request example

    使用端輸入想要中斷的任務ID

  ```bash
  curl -X 'POST' \
    'http://<api address>:<api port>/api/tasks/' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    	"TASK_ID": <task_id>
    }'
  
  ```

  + response example

  ```bash
  {
  	"error_code": 200,
  	"error_message" : f"successfully send break status to task <task_id> in state"
  }
  ```

  
