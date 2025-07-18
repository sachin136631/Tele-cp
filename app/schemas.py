from pydantic import BaseModel

class BugReportCreate(BaseModel):
    user_telegram_id: str
    username: str
    description: str
