## 專案架構

### 專案結構概覽

```
Backend/
├── main.py                    # FastAPI 應用程式入口點
├── requirements.txt           # Python 依賴套件清單
├── README.md                 # 專案說明文件
├── REDIS_SETUP_GUIDE.md      # Redis 設定指南
├── cache_performance_test.py # 快取效能測試腳本
├── test_redis_cache.py       # Redis 快取測試腳本
├── cache_performance_report.json # 快取效能報告
├── api/                      # API 路由模組
│   ├── __init__.py
│   ├── auth.py              # 使用者認證相關 API
│   ├── trade.py             # 交易系統相關 API
│   ├── fuzzy_search.py      # 語意模糊搜尋 API
│   └── cache.py             # 快取管理 API
├── core/                     # 核心功能模組
│   ├── __init__.py
│   ├── db.py                # 資料庫連線與初始化
│   ├── redis_client.py      # Redis 客戶端管理
│   ├── cache.py             # 快取裝飾器與管理
│   ├── graph_manager.py     # 交易圖形管理與路徑搜尋
│   └── limiter.py           # API 速率限制
├── models/                   # 資料模型定義
    ├── __init__.py
    ├── user_model.py        # 使用者資料模型
    └── user_schema.py       # 使用者資料驗證 Schema

```

### 各模組詳細說明

#### 1. 根目錄檔案

- **`main.py`**: FastAPI 應用程式的主要入口點，負責：
  - 初始化 FastAPI 應用程式
  - 設定路由器和中介軟體
  - 管理應用程式生命週期事件（啟動/關閉）
  - 整合所有 API 模組

- **`requirements.txt`**: 專案依賴套件清單，包含：
  - FastAPI 和 Uvicorn（Web 框架）
  - Beanie 和 PyMongo（MongoDB 整合）
  - Redis 相關套件（快取功能）
  - OpenAI（語意搜尋）
  - 其他工具套件

#### 2. API 模組 (`api/`)

- **`auth.py`**: 使用者認證系統
  - 使用者註冊功能（密碼加密、重複檢查）
  - 使用者登入驗證
  - 整合速率限制保護

- **`trade.py`**: 交易系統核心功能
  - 建立新交易記錄
  - 查詢交易歷史
  - 取得所有可交易物品清單
  - 統計最頻繁交易配對
  - 交易圖形路徑搜尋
  - 整合快取機制提升效能

- **`fuzzy_search.py`**: 語意模糊搜尋功能
  - 使用 OpenAI Embeddings 進行語意相似度比對
  - 支援批次處理和快取機制
  - 提供可調整的搜尋參數（top_k, min_score）

- **`cache.py`**: 快取管理 API
  - 提供快取資訊查詢
  - 支援快取值的增刪改查
  - 快取模式清理功能
  - Redis 連線健康檢查

#### 3. 核心模組 (`core/`)

- **`db.py`**: 資料庫管理
  - MongoDB 連線初始化
  - Beanie ODM 設定
  - 資料庫生命週期管理
  - 交易圖形資料載入

- **`redis_client.py`**: Redis 客戶端管理
  - 非同步 Redis 連線管理
  - 支援 JSON 序列化/反序列化
  - 提供完整的 Redis 操作介面
  - 連線池和錯誤處理

- **`cache.py`**: 快取系統核心
  - 快取裝飾器實現
  - 快取鍵生成策略
  - 快取失效機制
  - 快取管理器類別

- **`graph_manager.py`**: 交易圖形管理
  - 交易關係圖形建構
  - 交易路徑搜尋演算法
  - 匯率計算與權重分析
  - 時間加權的邊權重計算

- **`limiter.py`**: API 速率限制
  - 基於 IP 位址的請求限制
  - 防止 API 濫用攻擊

#### 4. 資料模型 (`models/`)

- **`user_model.py`**: 使用者資料模型
  - 定義使用者文件結構
  - 整合 Beanie ODM
  - 支援 MongoDB 操作

- **`user_schema.py`**: 資料驗證 Schema
  - 註冊表單驗證
  - 登入表單驗證
  - 密碼確認驗證

### 技術架構特點

1. **微服務架構**: 模組化設計，各功能獨立開發和維護
2. **非同步處理**: 全面使用 async/await 提升效能
3. **快取策略**: 多層快取機制（Redis + 記憶體快取）
4. **圖形演算法**: 交易關係圖形化，支援複雜路徑搜尋
5. **AI 整合**: OpenAI Embeddings 實現語意搜尋
6. **效能監控**: 內建效能測試和報告機制
7. **安全性**: 密碼加密、速率限制、輸入驗證

---

## API 端點總覽

以下是主要的 API 功能摘要。

**API Base URL:** `http://127.0.0.1:8000`

### 1. 使用者註冊

-   **Endpoint:** `POST /api/auth/register`
-   **功能:** 建立一個新帳戶。
-   **Request Body (JSON):**
    ```json
    {
      "email": "user@example.com",
      "password": "a_password_longer_than_8_chars",
      "confirmPassword": "a_password_longer_than_8_chars"
    }
    ```
-   **Responses (JSON):**
    -   **成功:** `{ "code": 0 }`
    -   **失敗:**
        -   `{ "code": 1 }` (信箱已被註冊)
        -   `{ "code": 2 }` (密碼長度不足 8 個字)
        -   `{ "code": 3 }` (兩次輸入的密碼不相同)


### 2. 使用者登入

-   **Endpoint:** `POST /api/auth/login`
-   **功能:** 驗證使用者身份。
-   **Request Body (JSON):**
    ```json
    {
      "email": "user@example.com",
      "password": "your_password"
    }
    ```
-   **Responses (JSON):**
    -   **成功:** `{ "code": 0 }`
    -   **失敗:** `{ "code": 1 }` (信箱或密碼錯誤)

### 3. 語意模糊搜尋

-   **Endpoint:** `POST /api/search/fuzzy-search`
-   **功能:** 以 OpenAI Embeddings 進行「字意」相似比對，從所有可交易物品清單中（來源：/api/trade/get-all-items）找出與查詢最相近的物品名稱，並依相似度由高到低回傳字串列表。
-   **Request Body (JSON):**
    ```json
    {
      "q": "藍色籃子",
      "top_k": 10,
      "min_score": 0.2
    }
    ```
-   **Responses (JSON):**
    -   **成功:** 回傳字串陣列
    ```json
    [
      "藍色洗衣籃",
      "藍色收納籃",
      "藍紫色提籃"
    ]
    ```
    -   **失敗:** 回傳空陣列
    ```json
    []
    ```

---

