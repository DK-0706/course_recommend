# cache.py —— Redis 缓存封装
import json
import os
import redis

# 连接 Redis（默认 localhost:6379）
try:
    r = redis.Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    r.ping()
    REDIS_OK = True
    print("[Redis] 连接成功")
except Exception as e:
    REDIS_OK = False
    print(f"[Redis] 连接失败，缓存已禁用：{e}")


def cache_get(key):
    """读缓存，返回 Python 对象或 None"""
    if not REDIS_OK:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        print(f"[Redis] 读失败 {key}：{e}")
        return None


def cache_set(key, value, ttl=300):
    """写缓存，ttl 秒"""
    if not REDIS_OK:
        return
    try:
        r.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except Exception as e:
        print(f"[Redis] 写失败 {key}：{e}")


def cache_del(*keys):
    """删缓存"""
    if not REDIS_OK:
        return
    try:
        if keys:
            r.delete(*keys)
    except Exception as e:
        print(f"[Redis] 删失败：{e}")


def cache_del_pattern(pattern):
    """按模式删缓存，如 rec:student:*"""
    if not REDIS_OK:
        return
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception as e:
        print(f"[Redis] 批量删失败：{e}")
