## 一、使用工具

+ Docker
+ Redis
+ FastAPI
+ Celery
+ Scikit-learn

## 二、開發項目

**模型:**

+ audience_model_interface
+ rule-based models
  + keyword_model
  + regex_model

**worker:**

+ Celery task
  + label_data
    + 運用SQL分頁功能批次讀取資料、執行貼標並寫入對應之資料表。
    + 若任務完成或出錯，將狀態更新在任務追蹤資料表 (state)

**API:**

+ create_task: `/tasks/` 建立並運行非同步貼標任務，結果輸出至對應資料表。
+ task_list: `/tasks/` 查詢近 50 筆貼標任務資訊。
+ check_status: `/tasks/{task_id}` 查詢特定任務進度狀態，若任務完成則回傳貼標結果資料表名稱。
+ sample_result: `/tasks/{task_id}/sample` 回傳貼標任務抽樣結果。

**資料表**:

+ state: 儲存貼標任務資訊。
+ wh_panel_mapping_{db_name}: 儲存貼標結果。

## 三、產品使用說明

#### 貼標任務流程

圖

#### 產品使用說明

1. 安裝 docker 與 redis

   請參考 [Docker Guides](https://docs.docker.com/get-started/)

   ```bash
   $ docker run -d -p 6379:6379 redis
   ```

2. 設定專案環境

   ```bash
   $ cd <your project dir>
   $ pip install virtualenv
   
   # Setup virtual environment
   $ virtualenv venv
   
   # Activate environment
   $ venv\Scripts\activate
   
   # install packages
   $ pip install -r requirements.txt
   ```

3. 設定連線資訊

   新增 `.env` 檔案於根目錄

   ```
   HOST=<database host>
   PORT=<database port>
   USER=<database username>
   PASSWORD=<database password>
   INPUT_SCHEMA=<database schema where you want to label>
   OUTPUT_SCHEMA=<database schema where you want to store the result and state>
   ```

4. 啟動 celery worker 與 API

   請參考 [celery getting started](https://docs.celeryproject.org/en/stable/getting-started/introduction.html)

   ```bash
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

   ```bash
   $ python label_api.py
   
   INFO:     Started server process [16116]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   
   ```

#### API 說明

+ create_task: `/tasks/`

  + Request: 
    + model_type: 模型類型
    + predict_type: 目標貼標欄位
    + start_time: 開始時間(任務貼目標擷取資料起始時間)
    + end_time: 結束時間(任務貼目標擷取資料結束時間)
    + target_schema: 目標資料庫
    + target_table: 目標資料表
    + date_info:  設定 true 則套用 start_time, end_time; 設定 false 不套用起始與結束，貼標範圍為整個資料表
    + batch_size: 批次執行資料大小

  ```bash
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
    "date_info": true,
    "batch_size": 1000000
  }'
  ```

  + Response:

  ```bash
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

+ task_list: `/tasks/`

  + Request

  ```bash
  curl -X 'GET' \
    'http://127.0.0.1:8000/api/tasks/' \
    -H 'accept: application/json'
  ```

  + Response

  ```bash
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
    ...
  }
  
  ```

+ check_status: `/tasks/{task_id}`

  + Request

  ```bash
  curl -X 'GET' \
    'http://127.0.0.1:8000/api/tasks/b773c786320c11eca0ca04ea56825bad' \
    -H 'accept: application/json'
  ```

  + Response

  ```bash
  {
    "SUCCESS": "wh_panel_mapping_Dcard,wh_panel_mapping_forum"
  }
  ```

+ sample_result: `/tasks/{task_id}/sample/`

  + Request

  ```bash
  curl -X 'GET' \
    'http://127.0.0.1:8000/api/tasks/988b791b32d911eca68704ea56825bad/sample/?table_name=wh_panel_mapping_Dcard&table_name=wh_panel_mapping_forum' \
    -H 'accept: application/json'
  
  ```

  + Response

  ```bash
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
  
  ```

#### Error code

