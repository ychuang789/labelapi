## 一、需求

因應 AS1 族群貼標需求，開發族群貼標任務 API

## 二、目標

需要開發兩個主要部分，貼標模型與任務 API，模型需包含: 

+ 關鍵字模型 Regex Model
+ 正則表達式模型 Keyword Model

兩個模型均能透過欄位參數與規則進行貼標，模型須至少具有讀取規則與預測結果兩個方法。

API 功能有，進行貼標任務、查詢單筆任務進度、查詢近期多筆任務資訊以及抽樣貼標內容。

貼標任務需支援背景運算。

## 三、開發項目

模型: 

+ Regex Model
+ Keyword Model

API:

+ create_task 需支援背景運算功能
+ task_list
+ check_status
+ sample_result

celery worker:

+ label_data
