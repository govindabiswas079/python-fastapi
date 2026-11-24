import asyncio
import json
import time

from app.core.config import settings


class EphemeralStore:
    def __init__(self):
        self._redis = None
        self._values = {}
        self._lock = asyncio.Lock()

    async def connect(self):
        if settings.REDIS_URL:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()

    async def close(self):
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def _get(self, key):
        if self._redis:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        async with self._lock:
            item = self._values.get(key)
            if not item:
                return None
            value, expires_at = item
            if expires_at <= time.time():
                self._values.pop(key, None)
                return None
            return value

    async def _set(self, key, value, ttl):
        if self._redis:
            await self._redis.set(key, json.dumps(value), ex=ttl)
            return
        async with self._lock:
            self._values[key] = (value, time.time() + ttl)

    # async def has_pending(self, email, phone):
    #     email_key, phone_key = f"pending:email:{email}", f"pending:phone:{phone}"
    #     if self._redis:
    #         return bool(await self._redis.exists(email_key, phone_key))
    #     return bool(await self._get(email_key) or await self._get(phone_key))

    async def create_pending(self, email, phone, data, ttl):
        email_key, phone_key = f"pending:email:{email}", f"pending:phone:{phone}"
        if self._redis:
            # Check and claim both identifiers atomically to avoid concurrent duplicate signups.
            script = """
            if redis.call('EXISTS', KEYS[1]) == 1 or redis.call('EXISTS', KEYS[2]) == 1 then
                return 0
            end
            redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
            redis.call('SET', KEYS[2], ARGV[3], 'EX', ARGV[2])
            return 1
            """
            result = await self._redis.eval(
                script, 2, email_key, phone_key, json.dumps(data), ttl, email
            )
            return bool(result)
        async with self._lock:
            await self._purge_local(email_key)
            await self._purge_local(phone_key)
            if email_key in self._values or phone_key in self._values:
                return False
            expires_at = time.time() + ttl
            self._values[email_key] = (data, expires_at)
            self._values[phone_key] = (email, expires_at)
            return True

    async def get_pending(self, email):
        return await self._get(f"pending:email:{email}")

    async def delete_pending(self, email, phone):
        keys = [f"pending:email:{email}", f"pending:phone:{phone}"]
        if self._redis:
            await self._redis.delete(*keys)
            return
        async with self._lock:
            for key in keys:
                self._values.pop(key, None)

    async def _purge_local(self, key):
        item = self._values.get(key)
        if item and item[1] <= time.time():
            self._values.pop(key, None)

    async def set_session(self, session_id, user_id, ttl):
        await self._set(f"session:{session_id}", user_id, ttl)

    async def get_session(self, session_id):
        return await self._get(f"session:{session_id}")

    async def consume_session(self, session_id):
        key = f"session:{session_id}"
        if self._redis:
            # GETDEL makes refresh-token rotation atomic.
            value = await self._redis.eval(
                "local v=redis.call('GET',KEYS[1]); if v then redis.call('DEL',KEYS[1]) end; return v",
                1,
                key,
            )
            return json.loads(value) if value else None
        async with self._lock:
            item = self._values.pop(key, None)
            if not item or item[1] <= time.time():
                return None
            return item[0]


ephemeral_store = EphemeralStore()


def otp_lifetime_seconds() -> int:
    return 10 * 60


def refresh_lifetime_seconds() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
