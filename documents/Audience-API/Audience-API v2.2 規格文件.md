## 一、需求

此版本為因應 Audience 站台對接而發佈的改良版本，目標讓 Audience 站台可以正確串接使用 Audience API 。

## 二、目標

+ 修改各項現有 API 服務，使 API 能及時接收和回傳站台請求資訊。
+ 新增 API 功能，支援提前中斷任務。
+ 任務追蹤資料表加上錯誤訊息欄位，以利後續維護。

## 三、開發項目

**1. 新增**

​	**API**

+ abort_task 

​    **Database**

+ state : error_message 

​    **Worker**

+ dump_result 

**2. 改良**

​	**API**

+ create_task

+ check_status

+ result_sample

  

