# 登入/註冊系統後端服務

這是一個使用 Node.js、Express 和 MongoDB 建立的後端服務，提供使用者註冊和登入的 API。

## ✨ 功能

-   使用者註冊
-   使用者登入
-   密碼加密儲存

## 🚀 技術棧

-   **執行環境:** [Node.js](https://nodejs.org/)
-   **網頁框架:** [Express.js](https://expressjs.com/)
-   **資料庫:** [MongoDB](https://www.mongodb.com/)
-   **ODM (物件資料模型):** [Mongoose](https://mongoosejs.com/)
-   **密碼加密:** [Bcrypt.js](https://github.com/dcodeIO/bcrypt.js)
-   **環境變數管理:** [Dotenv](https://github.com/motdotla/dotenv)
-   **跨來源資源共用:** [CORS](https://github.com/expressjs/cors)

## 📂 專案結構

```
.
├── server.js               # 伺服器主入口檔案，負責啟動服務、連接資料庫
├── package.json            # 專案設定與套件依賴清單
├── .env                    # (需手動建立) 環境變數檔案，存放資料庫連線資訊
├── controllers             # 存放核心業務邏輯
│   └── authController.js   # 處理註冊和登入的邏輯
├── models                  # 存放資料庫模型 (Schema)
│   └── User.js             # 定義使用者資料在資料庫中的結構
└── routes                  # 存放 API 路由設定
    └── auth.js             # 定義 /register 和 /login 路由
```

---

## 🛠️ 快速開始

### 1. 前置準備

請確保您的開發環境中已安裝 [Node.js](https://nodejs.org/) (建議版本 > 14.x) 和 [MongoDB](https://www.mongodb.com/try/download/community)。

### 2. 安裝依賴

在專案根目錄下，執行以下指令安裝所有必要的套件：

```bash
npm install
```

### 3. 設定環境變數

在專案根目錄下，手動建立一個名為 `.env` 的檔案，並填入您的 MongoDB Atlas 連線字串：

```
MONGO_URI=mongodb+srv://<你的使用者名稱>:<你的密碼>@<你的cluster網址>/<你的資料庫名稱>?retryWrites=true&w=majority
PORT=5000
```
> **注意:** 請務必將 `<...>` 部分替換成您自己的真實資訊。

### 4. 啟動伺服器

執行以下指令來啟動後端伺服器：

```bash
npm start
```

當您在終端機看到以下訊息時，表示伺服器已成功啟動：

```
MongoDB Connected...
Server started on port 5000
```

## 🔌 API 端點說明

### 註冊 (Register)

-   **URL:** `/api/auth/register`
-   **Method:** `POST`
-   **Body (Request):**
    ```json
    {
      "email": "test@example.com",
      "password": "password123",
      "confirmPassword": "password123"
    }
    ```
-   **Body (Response):**
    -   **成功:** `{ "code": 0 }`
    -   **失敗:**
        -   `{ "code": 1 }` (信箱已被註冊)
        -   `{ "code": 2 }` (密碼長度不足 8 個字)
        -   `{ "code": 3 }` (兩次輸入的密碼不相同)

### 登入 (Login)

-   **URL:** `/api/auth/login`
-   **Method:** `POST`
-   **Body (Request):**
    ```json
    {
      "email": "test@example.com",
      "password": "password123"
    }
    ```
-   **Body (Response):**
    -   **成功:** `{ "code": 0 }`
    -   **失敗:** `{ "code": 1 }` (信箱或密碼錯誤)
