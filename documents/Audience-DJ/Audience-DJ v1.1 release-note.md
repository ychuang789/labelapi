## 一、使用工具

+ django 3.1.13
+ djangorestframework 3.12.4

## 二、開發項目

#### predicting_jobs

+ `predicting_jobs.tasks`: 新增串接 Audience-API 功能
+ `predicting_jobs.views`: 
  + 新增
    + render_sample_results 查詢抽樣結果
    + render_all_status 查詢 job 所有目標來源貼標任務資訊與狀態
    + render_status 查詢單筆貼標任務資訊與狀態
  + 修改
    + start_job 移除舊功能，串接 Audience-API
    + cancel_job  移除舊功能，串接 Audience-API 支援使用者可以外部中斷任務
    + get_progress 充呼叫Audience-API 檢查任務進度功能，並能刷新任務狀態
  + 刪除
    + `PredictResultSamplingListView`
+ `predicting_jobs template`: 
  + 新增結果抽樣頁面
  + 新增任務資訊頁面

## 三、產品使用說明

使用者介面操作方法請參考

+ 