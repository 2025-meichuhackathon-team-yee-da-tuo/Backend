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
