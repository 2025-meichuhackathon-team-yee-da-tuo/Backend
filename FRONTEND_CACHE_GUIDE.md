# 前端快取策略指南

## 概述

本指南說明如何在前端實作快取策略，與後端 Redis 快取系統配合使用，提供最佳的使用者體驗。

## 前端快取層級

### 1. HTTP 快取 (Browser Cache)
利用瀏覽器的 HTTP 快取機制：

```javascript
// 設定 Cache-Control headers
const cacheHeaders = {
  'Cache-Control': 'public, max-age=300', // 5 分鐘
  'ETag': 'unique-identifier'
};

// 使用 fetch 時設定快取
fetch('/api/trade/get-all-items', {
  headers: cacheHeaders
});
```

### 2. Service Worker 快取
實作 Service Worker 進行離線快取：

```javascript
// sw.js
const CACHE_NAME = 'meichu-cache-v1';
const urlsToCache = [
  '/api/trade/get-all-items',
  '/api/trade/collections',
  '/api/search/fuzzy-search'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
```

### 3. 記憶體快取 (In-Memory Cache)
使用 JavaScript 物件或 Map 進行記憶體快取：

```javascript
class MemoryCache {
  constructor(ttl = 300000) { // 5 分鐘預設 TTL
    this.cache = new Map();
    this.ttl = ttl;
  }

  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }

  clear() {
    this.cache.clear();
  }
}

// 使用範例
const cache = new MemoryCache();

async function getCachedData(url) {
  const cached = cache.get(url);
  if (cached) {
    console.log('從記憶體快取取得資料');
    return cached;
  }

  const response = await fetch(url);
  const data = await response.json();
  cache.set(url, data);
  return data;
}
```

### 4. LocalStorage/SessionStorage 快取
對於較穩定的資料使用本地儲存：

```javascript
class LocalStorageCache {
  constructor(prefix = 'meichu_') {
    this.prefix = prefix;
  }

  set(key, value, ttl = 3600000) { // 1 小時預設 TTL
    const item = {
      value,
      timestamp: Date.now(),
      ttl
    };
    localStorage.setItem(this.prefix + key, JSON.stringify(item));
  }

  get(key) {
    const itemStr = localStorage.getItem(this.prefix + key);
    if (!itemStr) return null;

    const item = JSON.parse(itemStr);
    if (Date.now() - item.timestamp > item.ttl) {
      localStorage.removeItem(this.prefix + key);
      return null;
    }

    return item.value;
  }

  remove(key) {
    localStorage.removeItem(this.prefix + key);
  }

  clear() {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => localStorage.removeItem(key));
  }
}
```

## React/Vue 快取實作範例

### React Hook 範例

```javascript
import { useState, useEffect, useCallback } from 'react';

function useCache(ttl = 300000) {
  const [cache, setCache] = useState(new Map());

  const getCached = useCallback((key) => {
    const item = cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > ttl) {
      setCache(prev => {
        const newCache = new Map(prev);
        newCache.delete(key);
        return newCache;
      });
      return null;
    }

    return item.value;
  }, [cache, ttl]);

  const setCached = useCallback((key, value) => {
    setCache(prev => new Map(prev).set(key, {
      value,
      timestamp: Date.now()
    }));
  }, []);

  return { getCached, setCached };
}

// 使用範例
function TradeHistory() {
  const { getCached, setCached } = useCache();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    const cacheKey = 'trade-history';
    const cached = getCached(cacheKey);
    
    if (cached) {
      setData(cached);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/trade/trade-history');
      const result = await response.json();
      setCached(cacheKey, result);
      setData(result);
    } catch (error) {
      console.error('取得資料失敗:', error);
    } finally {
      setLoading(false);
    }
  }, [getCached, setCached]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div>
      {loading ? <div>載入中...</div> : <div>{/* 顯示資料 */}</div>}
    </div>
  );
}
```

### Vue Composable 範例

```javascript
// composables/useCache.js
import { ref, computed } from 'vue';

export function useCache(ttl = 300000) {
  const cache = ref(new Map());

  const getCached = (key) => {
    const item = cache.value.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > ttl) {
      cache.value.delete(key);
      return null;
    }

    return item.value;
  };

  const setCached = (key, value) => {
    cache.value.set(key, {
      value,
      timestamp: Date.now()
    });
  };

  const clearCache = () => {
    cache.value.clear();
  };

  return {
    getCached,
    setCached,
    clearCache
  };
}

// 使用範例
// components/TradeHistory.vue
<template>
  <div>
    <div v-if="loading">載入中...</div>
    <div v-else>{{ data }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useCache } from '@/composables/useCache';

const { getCached, setCached } = useCache();
const data = ref(null);
const loading = ref(false);

const fetchData = async () => {
  const cacheKey = 'trade-history';
  const cached = getCached(cacheKey);
  
  if (cached) {
    data.value = cached;
    return;
  }

  loading.value = true;
  try {
    const response = await fetch('/api/trade/trade-history');
    const result = await response.json();
    setCached(cacheKey, result);
    data.value = result;
  } catch (error) {
    console.error('取得資料失敗:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>
```

## 快取策略建議

### 1. 資料類型對應的快取策略

| 資料類型 | 快取層級 | TTL | 說明 |
|---------|---------|-----|------|
| 物品清單 | LocalStorage + Memory | 10 分鐘 | 相對穩定，可長期快取 |
| 交易歷史 | Memory | 5 分鐘 | 經常變動，短期快取 |
| 搜尋結果 | Memory | 10 分鐘 | 基於查詢，可適度快取 |
| 使用者資料 | LocalStorage + Memory | 30 分鐘 | 個人資料，可較長快取 |

### 2. 快取失效策略

```javascript
// 當新增交易時，清除相關快取
function invalidateTradeCache() {
  // 清除記憶體快取
  memoryCache.clear();
  
  // 清除本地儲存快取
  localStorageCache.clear();
  
  // 通知其他頁面清除快取
  window.dispatchEvent(new CustomEvent('cache-invalidate'));
}

// 監聽快取失效事件
window.addEventListener('cache-invalidate', () => {
  // 重新載入資料
  fetchData();
});
```

### 3. 網路狀態感知快取

```javascript
// 檢測網路狀態
function isOnline() {
  return navigator.onLine;
}

// 根據網路狀態調整快取策略
function getCacheStrategy() {
  if (isOnline()) {
    return {
      useMemoryCache: true,
      useLocalStorage: true,
      ttl: 300000 // 5 分鐘
    };
  } else {
    return {
      useMemoryCache: true,
      useLocalStorage: true,
      ttl: 3600000 // 1 小時（離線時延長快取）
    };
  }
}
```

## 最佳實踐

1. **分層快取**: 結合多種快取策略，提供最佳效能
2. **適當的 TTL**: 根據資料特性設定合適的過期時間
3. **快取失效**: 當資料更新時及時清除相關快取
4. **錯誤處理**: 快取失敗時要有降級策略
5. **記憶體管理**: 定期清理過期的快取項目
6. **使用者體驗**: 提供快取狀態的視覺回饋

## 監控和除錯

```javascript
// 快取統計
class CacheStats {
  constructor() {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0
    };
  }

  hit() { this.stats.hits++; }
  miss() { this.stats.misses++; }
  set() { this.stats.sets++; }
  delete() { this.stats.deletes++; }

  getHitRate() {
    const total = this.stats.hits + this.stats.misses;
    return total > 0 ? this.stats.hits / total : 0;
  }

  getStats() {
    return {
      ...this.stats,
      hitRate: this.getHitRate()
    };
  }
}

// 使用範例
const cacheStats = new CacheStats();

// 在快取操作時記錄統計
function getCached(key) {
  const item = cache.get(key);
  if (item) {
    cacheStats.hit();
    return item;
  } else {
    cacheStats.miss();
    return null;
  }
}
```

這個指南提供了完整的前端快取實作方案，可以與後端 Redis 快取系統配合使用，提供優異的使用者體驗。
