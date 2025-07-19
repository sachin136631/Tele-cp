from fastapi import FastAPI, Depends, HTTPException,Path
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, BugReport
from app.schemas import BugReportCreate

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/report-bug")
def report_bug(bug: BugReportCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == bug.user_telegram_id).first()
    if not user:
        user = User(telegram_id=bug.user_telegram_id, username=bug.username)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    new_bug = BugReport(
        user_id=user.id,
        title=bug.description[:30],  # Optional short title
        description=bug.description,
        status="open"  # Default status
        # timestamp is auto-generated
    )
    db.add(new_bug)
    db.commit()
    db.refresh(new_bug)

    return {
        "message": "Bug reported successfully",
        "bug_id": new_bug.id,
        "status": new_bug.status
    }



@app.get("/bugs")
def list_bugs(db: Session = Depends(get_db)):
    bugs = db.query(BugReport).all()
    return [
        {
            "id": bug.id,
            "description": bug.description,
            "status": bug.status
        }
        for bug in bugs
    ]


@app.put("/bug/{bug_id}")
def update_bug_status(bug_id: int, status: str, db: Session = Depends(get_db)):
    bug = db.query(BugReport).filter(BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    bug.status = status
    db.commit()
    return {"message": f"Bug {bug_id} updated to {status}"}


@app.get("/user-bugs/{telegram_id}")
def get_user_bugs(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bugs = db.query(BugReport).filter(
        BugReport.user_id == user.id
    ).order_by(BugReport.timestamp.desc()).all()

    return [
        {
            "id": bug.id,
            "description": bug.description,
            "status": bug.status,
            "created_at": bug.timestamp
        }
        for bug in bugs
    ]

@app.delete("/delete-bug/{bug_id}")
def delete_bug(bug_id: int, db: Session = Depends(get_db)):
    bug = db.query(BugReport).filter(BugReport.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    db.delete(bug)
    db.commit()
    return {"detail": f"Bug {bug_id} deleted successfully"}