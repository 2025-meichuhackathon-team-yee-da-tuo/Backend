# Redis 快取系統設定指南

## 概述

本指南將協助你設定 Redis 快取系統，包括本地安裝和雲端服務設定。

## 1. 本地 Redis 安裝

### macOS (使用 Homebrew)
```bash
# 安裝 Redis
brew install redis

# 啟動 Redis 服務
brew services start redis

# 驗證安裝
redis-cli ping
# 應該回傳 PONG
```

### Ubuntu/Debian
```bash
# 更新套件列表
sudo apt update

# 安裝 Redis
sudo apt install redis-server

# 啟動 Redis 服務
sudo systemctl start redis-server

# 設定開機自動啟動
sudo systemctl enable redis-server

# 驗證安裝
redis-cli ping
```

### Windows
1. 下載 Redis for Windows: https://github.com/microsoftarchive/redis/releases
2. 解壓縮並執行 `redis-server.exe`
3. 開啟新的命令提示字元執行 `redis-cli.exe ping`

### Docker 方式
```bash
# 執行 Redis 容器
docker run -d --name redis-cache -p 6379:6379 redis:latest

# 驗證連線
docker exec -it redis-cache redis-cli ping
```

## 2. 雲端 Redis 服務

### Redis Cloud
1. 前往 https://redis.com/try-free/
2. 註冊帳號並建立免費資料庫
3. 取得連線資訊：
   - Host: xxx.redis.cloud.redislabs.com
   - Port: xxxxx
   - Password: xxxxx

### AWS ElastiCache
1. 在 AWS 控制台建立 ElastiCache 叢集
2. 選擇 Redis 引擎
3. 設定安全群組允許 6379 埠連線

### Google Cloud Memorystore
1. 在 GCP 控制台建立 Memorystore Redis 實例
2. 設定網路和防火牆規則

## 3. 環境變數設定

建立 `.env` 檔案（參考 `env_example.txt`）：

```bash
# 本地 Redis
REDIS_URL=redis://localhost:6379

# 雲端 Redis (Redis Cloud 範例)
REDIS_URL=redis://username:password@host:port

# 帶 SSL 的雲端 Redis
REDIS_URL=rediss://username:password@host:port
```

## 4. 安裝 Python 依賴

```bash
# 進入專案目錄
cd /Users/jen/Desktop/Code/meichu_2025/Backend

# 啟動虛擬環境
source venv/bin/activate

# 安裝 Redis 相關套件
pip install "redis[hiredis]"

# 或使用 requirements.txt
pip install -r requirements.txt
```

## 5. 測試 Redis 連線

建立測試腳本 `test_redis.py`：

```python
import asyncio
import os
from dotenv import load_dotenv
from core.redis_client import redis_client

load_dotenv()

async def test_redis():
    try:
        # 連線到 Redis
        await redis_client.connect()
        print("✅ Redis 連線成功!")
        
        # 測試基本操作
        await redis_client.set("test_key", "Hello Redis!", expire=60)
        value = await redis_client.get("test_key")
        print(f"✅ 設定和取得值: {value}")
        
        # 測試 JSON 資料
        test_data = {"name": "測試", "value": 123, "items": [1, 2, 3]}
        await redis_client.set("test_json", test_data, expire=60)
        json_value = await redis_client.get("test_json")
        print(f"✅ JSON 資料: {json_value}")
        
        # 測試雜湊表
        await redis_client.hset("test_hash", {"field1": "value1", "field2": "value2"})
        hash_value = await redis_client.hget("test_hash", "field1")
        print(f"✅ 雜湊表值: {hash_value}")
        
        # 清理測試資料
        await redis_client.delete("test_key")
        await redis_client.delete("test_json")
        await redis_client.delete("test_hash")
        print("✅ 測試資料已清理")
        
    except Exception as e:
        print(f"❌ Redis 測試失敗: {e}")
    finally:
        await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_redis())
```

執行測試：
```bash
python test_redis.py
```

## 6. 啟動應用程式

```bash
# 確保 Redis 服務正在運行
redis-cli ping

# 啟動 FastAPI 應用程式
python main.py
```

## 7. 驗證快取功能

### 使用 API 測試快取

1. **測試快取管理 API**：
```bash
# 取得快取資訊
curl http://localhost:8000/api/cache/info

# 設定快取值
curl -X POST http://localhost:8000/api/cache/set \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "Hello World", "ttl": 300}'

# 取得快取值
curl http://localhost:8000/api/cache/get/test

# 清空所有快取
curl -X DELETE http://localhost:8000/api/cache/clear-all
```

2. **測試交易 API 快取**：
```bash
# 第一次請求（會執行資料庫查詢並快取）
curl http://localhost:8000/api/trade/get-all-items

# 第二次請求（會從快取取得）
curl http://localhost:8000/api/trade/get-all-items
```

### 使用 Redis CLI 監控

```bash
# 連線到 Redis
redis-cli

# 查看所有鍵
KEYS *

# 查看特定模式的鍵
KEYS trade:*

# 查看鍵的 TTL
TTL trade:all_items

# 查看鍵的值
GET trade:all_items

# 監控 Redis 命令
MONITOR
```

## 8. 效能監控

### Redis 資訊命令
```bash
# 連線到 Redis CLI
redis-cli

# 查看 Redis 資訊
INFO

# 查看記憶體使用情況
INFO memory

# 查看統計資訊
INFO stats

# 查看慢查詢日誌
SLOWLOG GET 10
```

### 設定 Redis 監控
```python
# 在應用程式中添加監控
import time
from core.redis_client import redis_client

async def monitor_redis_performance():
    start_time = time.time()
    
    # 執行 Redis 操作
    await redis_client.set("monitor_test", "test_value")
    value = await redis_client.get("monitor_test")
    
    end_time = time.time()
    print(f"Redis 操作耗時: {(end_time - start_time) * 1000:.2f}ms")
```

## 9. 故障排除

### 常見問題

1. **連線被拒絕**
   ```
   redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379
   ```
   - 檢查 Redis 服務是否啟動
   - 檢查防火牆設定
   - 確認埠號是否正確

2. **認證失敗**
   ```
   redis.exceptions.AuthenticationError: Authentication required
   ```
   - 檢查 Redis 密碼設定
   - 確認環境變數中的密碼正確

3. **記憶體不足**
   ```
   redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'
   ```
   - 增加 Redis 記憶體限制
   - 清理過期的快取資料
   - 調整快取 TTL 設定

4. **Python 3.13 相容性問題**
   ```
   ModuleNotFoundError: No module named 'distutils'
   ```
   - 使用 `redis[hiredis]` 而不是 `aioredis`
   - 確保使用最新版本的 redis 套件
   - 如果仍有問題，可以降級到 Python 3.11 或 3.12

### 除錯技巧

1. **啟用 Redis 日誌**
   ```bash
   # 編輯 Redis 設定檔
   sudo nano /etc/redis/redis.conf
   
   # 設定日誌等級
   loglevel notice
   
   # 重啟 Redis 服務
   sudo systemctl restart redis-server
   ```

2. **使用 Redis 除錯工具**
   ```bash
   # 檢查 Redis 連線
   redis-cli --latency-history -i 1
   
   # 檢查記憶體使用
   redis-cli --bigkeys
   
   # 檢查慢查詢
   redis-cli --latency
   ```

## 10. 生產環境建議

1. **安全性設定**
   - 設定 Redis 密碼
   - 限制網路存取
   - 使用 SSL/TLS 連線

2. **效能優化**
   - 設定適當的記憶體限制
   - 啟用記憶體淘汰策略
   - 監控慢查詢

3. **備份策略**
   - 定期備份 Redis 資料
   - 設定主從複製
   - 監控 Redis 健康狀態

4. **監控和告警**
   - 設定記憶體使用告警
   - 監控連線數
   - 追蹤快取命中率

完成以上設定後，你的 Redis 快取系統就可以正常運作了！
