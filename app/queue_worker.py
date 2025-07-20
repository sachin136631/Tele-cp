import asyncio
import json
import os
import redis.asyncio as redis
from database import SessionLocal
from models import BugReport, User  # Make sure User is imported

r = redis.from_url(os.getenv("REDIS_URL"))
QUEUE_KEY = "bug_queue"

async def process_queue():
    print("********************worker has started working********")
    while True:
        _, data = await r.blpop(QUEUE_KEY)
        bug_data = json.loads(data)
        print("processing bug ", bug_data)
        db = SessionLocal()
        try:
            # Ensure the user exists
            telegram_id = str(bug_data.get("telegram_id") or bug_data.get("user_telegram_id"))
            user = db.query(User).filter(User.telegram_id == telegram_id).first()

            if not user:
                user = User(
                    id=bug_data["telegram_id"],  # ensure this is INT if `id` is INT
                    telegram_id=telegram_id
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # Insert the bug report using user's actual DB id
            bug = BugReport(
                user_id=user.id,
                title=bug_data["description"],
                description=bug_data["description"],
                status="open"
            )
            db.add(bug)
            db.commit()
            db.refresh(bug)
            print("inserted")


        except Exception as e:
            print("DB Error", e)
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(process_queue())
