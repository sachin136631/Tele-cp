from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base, SessionLocal
from sqlalchemy.orm import relationship

class BugReport(Base):
    __tablename__ = 'bug_reports'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String, default="open")
    timestamp = Column(DateTime, default=func.now())  # uses DB time

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="bug_reports")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)

    bug_reports = relationship("BugReport", back_populates="user")

def init_db():
    Base.metadata.create_all(bind=SessionLocal().get_bind())

async def save_bug_report(user_id: str, summary: str) -> int:
    db = SessionLocal()
    bug = BugReport(title=summary[:30], description=summary, user_id=user_id)
    db.add(bug)
    db.commit()
    db.refresh(bug)
    db.close()
    return bug.id
