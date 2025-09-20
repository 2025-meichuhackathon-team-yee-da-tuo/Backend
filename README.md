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

---
