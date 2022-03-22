##  一、使用工具

+ FastAPI
+ Celery

## 二、開發項目

**worker:**

+ Celery task
  + label_data
    + 修改批次查詢功能，前版本 `get_data_by_batch` 需先取的目標查詢總數，在使用 offset 批次翻頁查詢資料；此版本改為 `get_batch_by_timedelta`，使用時間索引批次查詢目標資料，預設每六小時為區間。降低額外查詢所耗費的資源與時間。
  + generate_production
    + 產出驗證結果，如目標資料長度、結果資料長度、貼標率、不重複作者數等
    + 清理重複資料

**API:**

+ create_task: `/tasks/` 加入 generate_production 步驟。

**資料表**:

+ state: 增加驗證結果等欄位。
+ temp: 新增各個 temp 資料表，與 generate_production 結果資料表區分。

## 三、產品使用說明

#### 貼標任務流程

圖

#### 產品使用說明

見 Audience-API v2.0 release-note

.env 修改

使用 docs

