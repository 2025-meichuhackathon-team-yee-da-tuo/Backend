# 登入/註冊系統後端服務 (Python/FastAPI 版本)

這是一個使用 Python、FastAPI 和 MongoDB 建立的高效能後端服務，提供使用者註冊和登入的 API。

## ✨ 功能

-   使用者註冊
-   使用者登入
-   密碼安全雜湊儲存
-   基於 Pydantic 的請求資料自動驗證
-   自動產生的互動式 API 文件 (Swagger UI & ReDoc)

## 🚀 技術棧

-   **Web 框架:** [FastAPI](https://fastapi.tiangolo.com/)
-   **資料庫:** [MongoDB](https://www.mongodb.com/)
-   **非同步 ODM:** [Beanie](https://github.com/roman-right/beanie)
-   **密碼雜湊:** [Bcrypt](https://github.com/pyca/bcrypt/)
-   **環境變數管理:** [Python-Dotenv](https://github.com/theskumar/python-dotenv)
-   **ASGI 伺服器:** [Uvicorn](https://www.uvicorn.org/)

## 📂 專案結構

```
.
├── main.py                 # 主應用程式入口，負責整合所有元件
├── api                     # 存放所有 API 路由 (Endpoints)
│   └── auth.py
├── core                    # 存放核心設定，例如資料庫連線
│   └── db.py
├── models                  # 存放所有資料模型
│   ├── user_model.py       # Beanie 資料庫模型 (對應 MongoDB)
│   └── user_schema.py      # Pydantic 資料驗證模型 (用於 API)
├── requirements.txt        # Python 套件依賴清單
└── .env                    # (需手動建立) 環境變數檔案
```

---

## 🛠️ 快速開始

### 1. 前置準備

請確保您的開發環境中已安裝 [Python](https://www.python.org/) (建議版本 > 3.8)。

### 2. (建議) 建立並啟用虛擬環境

在專案根目錄下，執行以下指令來建立一個獨立的 Python 環境，避免套件與系統全域套件衝突。

```bash
# 建立虛擬環境 (資料夾名稱為 venv)
python -m venv venv

# 在 MacOS / Linux 上啟用虛擬環境
source venv/bin/activate

# 在 Windows (cmd.exe) 上啟用虛擬環境
# venv\Scripts\activate.bat
```
啟用成功後，您的終端機提示字元前會出現 `(venv)`。

### 3. 安裝依賴

執行以下指令安裝所有必要的 Python 套件：

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數

在專案根目錄下，手動建立一個名為 `.env` 的檔案，並填入您的 MongoDB Atlas 連線字串。

```
MONGO_URI=mongodb+srv://<你的使用者名稱>:<你的密碼>@<你的cluster網址>/<你的資料庫名稱>?retryWrites=true&w=majority
```

### 5. 啟動伺服器

執行以下指令來啟動後端開發伺服器：

```bash
uvicorn main:app --reload
```
-   `main`: 指的是 `main.py` 檔案。
-   `app`: 指的是在 `main.py` 中建立的 FastAPI 實例 `app = FastAPI()`。
-   `--reload`: 啟用熱重載，當您修改程式碼並存檔時，伺服器會自動重啟。

伺服器預設會運行在 `http://127.0.0.1:8000`。

## 🔌 API 端點測試

請打開您的瀏覽器，然後前往 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

您會看到一個 Swagger UI 頁面，其中列出了我們所有的 API 端點。由於我們進行了模組化，路由現在會被分類在 `Authentication` 標籤下，並且路徑會是完整的 `/api/auth/register` 和 `/api/auth/login`。

您可以直接在這個頁面上進行所有功能的測試。
