## 需求

此版本為因應 Audience 站台對接而發佈的改良版本，目標讓 Audience 站台可以正確串接使用 Audience API 。

## 開發項目

**1. 新增**

​	**API**

+ abort_task : 支援使用者可以提前中斷任務。

​    **Database**

+ 任務資料表 : 新增 error_message 欄位。



**2. 改良**

​	**API**

+ create_task : 舊版規則與連線寫在內部程式，此版本調整 API request 參數，支援使用者帶入外部規則與資料庫連線資訊。

+ check_status : 舊版僅回傳任務進度狀態，此版本除了能回傳狀態之外支援回傳任務所有資訊，包含開始時間、任務結果統計資訊、錯誤訊息等等。

+ result_sample : 舊版僅支持任務完成抽樣結果，此版本修改為能隨時抽樣貼標結果。

  

**3. 刪除**

​	**Worker**

+ 移除 dump 功能

