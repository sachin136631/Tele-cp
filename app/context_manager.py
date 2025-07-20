import redis.asyncio as redis
import os
import json
 
r=redis.from_url(os.getenv("REDIS_URL"))

async def add_message(user_id:str,message:str):
    key=f"ctx:{user_id}"
    await r.rpush(key,message)
    await r.expire(key,3600)

async def get_full_context(user_id: str):
    key = f"ctx:{user_id}"
    messages = await r.lrange(key, 0, -1)
    return "\n".join(m.decode('utf-8') for m in messages)

    