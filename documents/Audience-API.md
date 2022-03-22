## 一、產品描述

建立可以支援 Audience 內部專案使用者操作的 API 功能，取代 Audience 站台服務計算功能，預計實現前後端程式分離。

## 二、產品目標

使用 Python Fast API 依以下順序建立 API  :

+ 貼標任務
+ 模型操作
+ 資料整備

產品初步目標讓使用者能呼叫 API 完成貼標工作，其次加入模型訓練、驗證、預測功能，最後是開發讓使用者可以操作之資料整備介面。部分 API 如貼標任務、模型訓練等可以透過使用後端任務佇列系統 Celery 執行背景運算來輔助，記錄和回傳任務與資料運算結果，供使用者可以檢驗資料抽樣內容，調整模型訓練或規則資料。

## 三、系統架構與任務流程

#### 1. 專案系統

#### 2. 貼標任務

###### 實體關聯設定

###### 任務流程

#### 3. 模型操作

###### 實體關聯設定

###### 任務流程



## 四、產品說明

#### 1. 安裝說明

此專案使用 Python 3.8 於 Windows 10 與 Ubuntu 18.04.5 開發與測試，請預先安裝以下工具 :

+ Docker 

  + [windows 安裝教學](https://docs.microsoft.com/zh-tw/windows/wsl/tutorials/wsl-containers)
  + [ubuntu 安裝教學](https://docs.docker.com/engine/install/ubuntu/)

+ Redis (docker-image)

  [redis 安裝](https://hub.docker.com/_/redis)

  ```bash
  $ docker run -d -p 6379:6379 redis
  ```

+ MariaDB

+ Python 3.8

  [Python 3.8 安裝](https://www.python.org/downloads/release/python-3810/)

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

#### 2. API 測試說明

###### API endpoints

1. tasks (Predicting)
2. models
3. preprocess

啟動 API 服務

```bash
# run the interactive swagger-ui to test the api by makefile
$ make run_api
# or
$ python audience_api.py
```

若要使用 celery worker

```bash
# 貼標任務
$ make run_predicting_1

# 模型任務
$ make run_modeling_1
```

開啟 swagger-ui 測試介面，在瀏覽器中輸入

`<API host:port>/docs`

例如本地端測試 : `127.0.0.1:8000/docs`

無法開啟 swagger-ui

+ [swagger-ui issue list](https://github.com/swagger-api/swagger-ui/issues)
+ [fastapi issue list](https://github.com/tiangolo/fastapi/issues)

圖

API 測試頁面

操作說明

[Swagger-ui 教學延伸資訊](https://swagger.io/tools/swagger-ui/)



## 五、開發指南

專案模組檔案目錄結構 :

```bash
Audience_API/
	apis/
		input_class/
			modeling_input.py
			predicting_input.py
		__init__.py
		modeling_api.py
		predicting_api.py
	graph/
    models/
    	rule_based_models/
    	trainable_models/
    	audience_model_interfaces.py
    tests/
	utils/
	workers/
		modeling/
		orm_core/
		predicting/
		preprocessing/
		worker_helper.py
	audience_api.py
	definition.py
	celery_worker.py
	Makefile
	requirements.in
	requirements.txt
	settings.py
	test.py
	...
```

### 1. 模型開發

若要新增現有類型模型 (規則模型、機器學習模型) 請參考 `models/audience_model_interfaces.py` ，繼承對應之介面，並於以下套件目錄下新增對應模型模組檔案:

+ `rule_based_models/`
+ `trainable_models/`

若要新增之模型不屬於現有類型，請在 `models/audience_model_interfaces.py` 新增抽象介面類，並在 `models/`路徑中新增該類型模型之套件資料夾，請參考以上資料夾。

模型模組檔案命名方式請依照 `<模型名稱>_model.py` 命名，模型類別請依駝峰式命名，如 `RandomForestModel`。
開發完成請在專案根目錄 `settings.py` 中 `MODEL_INFORMATION` 新增模型名稱 (與大寫檔案名稱相同) 與 模型類路徑，如 `"RANDOM_FOREST_MODEL": "models.trainable_models.rf_model.RandomForestModel"`

### 2. API 開發

若要新增 api 服務，請在 `apis/` 目錄下新增 api 模組檔案，例如 `modeling_api.py`，並於模組內加上:

```python
from fastapi import APIRouter

router = APIRouter(prefix='/<API 前綴>',
                   tags=['<API 標籤>'],
                   responses={404: {"description": "Not found"}},
                   )

```

並且在根目錄 audience_api.py 文件中加上以下:

```python
description = """
...
##### <服務名稱>
<API endpoints 介紹>
"""

app.include_router(<API 服務名稱>.router)
```

`apis/input_class/` 儲存所有 API 的 request class 資訊，若需要新增 response class 可以新增路徑 `apis/output_class` 或 `apis/response_class/`。

### 3. Worker 開發

#### CRUD worker

本專案使用 sqlalchemy orm 建立與操作資料表，若要新增資料表 schema 請在 `workers/orm_core/table_creator.py` 模組內新增資料類。

若要新增 CRUD 功能請 `workers/orm_core/` 目錄新增 `<服務名稱>_operation.py` 模組，創建 `<服務名稱>CRUD` 類別並繼承 `BaseOperation` 如:

```Python
from workers.orm_core.base_operation import BaseOperation

class ModelingCRUD(BaseOperation):
    def __init__(self)
    	...
```

#### 其他 worker

請於 `workers/` 目錄下新增想要建立的服務套件資料夾，建立模組檔案，如 `workers/modeling/model_core.py`，並建立類別 `<服務名稱>Worker`，如 `ModelingWorker`。

### 4. 測試程式開發

本專案使用 `unittest`與 `pytest`測試框架 (僅 api 測試使用 `pytest`)，若要新增測試程式，請在 `tests/` 找到對應的資料夾，如 `tests/worker/test_modeling_worker.py`，請記得測試模組標頭要加上 "test_"。

另外可以透過根目錄 `test.py` 快速透過 CLI 執行測試程式 ([Python CLI 文件](https://click.palletsprojects.com/en/8.0.x/))，請參考 `test.py --help` 

測試延伸教學

+ [unittest](https://docs.python.org/zh-tw/3/library/unittest.html)
+ [pytest](https://docs.pytest.org/en/7.1.x/)

### 5. 非同步任務系統開發

本專案使用 Celery 實現非同步任務佇列系統，相關任務內容在根目錄 `celery_worker.py`，若要開發 celery 任務程式或定時程式請參考 [Celery 文件](https://docs.celeryproject.org/en/stable/getting-started/index.html) 。

本專案 API 模型整備(訓練驗證)任務 `/models/prepare/` 與貼標任務 POST `/tasks/` 會使用 celery worker，若要測試請先啟動。 

啟動 celery worker 方法:

```bash
# 請參考根目錄 Makefile

# 貼標任務
$ make run_predicting_1

# 模型任務
$ make run_modeling_1
```

### 6. 其他開發

若要開發通用的小功能可以將其儲存於 `utils/` 套件資料夾。

Makefile 檔案紀錄重要的專案指令，若需編輯詳細可[參考教學](https://makefiletutorial.com/)。

若有安裝額外套件，須將其手動加入 `requirements.txt` 或是加入 `requirements.in` 再透過 `pip-complie` 指令寫入 `requirements.txt`。 



## 六、Release 文件

