import asyncio
import json
import os
import redis.asyncio as redis
from database import SessionLocal
from models import BugReport, User
from context_manager import add_message, get_full_context
from groq_client import summarize_bug

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
            # Extract telegram_id from either key
            telegram_id = str(bug_data.get("telegram_id") or bug_data.get("user_telegram_id"))

            # Ensure user exists
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(
                    id=int(telegram_id),  # Make sure this matches your DB model
                    telegram_id=telegram_id
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # Store the incoming bug message to context
            await add_message(telegram_id, bug_data["description"])

            # Retrieve full conversation context
            full_context = await get_full_context(telegram_id)

            # Get summarized version using Groq
            summary = summarize_bug(full_context)

            # Save summarized bug to DB
            bug = BugReport(
                user_id=user.id,
                title=summary[:100],  # or bug_data["description"][:100],
                description=summary,
                status="open"
            )
            db.add(bug)
            db.commit()
            db.refresh(bug)

            print("Saved summarized bug:", summary)

        except Exception as e:
            print("DB Error", e)
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    asyncio.run(process_queue())
