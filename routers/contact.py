from fastapi import APIRouter, Depends, HTTPException
from src.database_model import Contact, ContactInput
from src.database import Session1
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/contact",
    tags=["contact"],
)


def get_db():
    db = Session1()
    try:
        yield db
    finally:
        db.close()


@router.post("/submit")
def submit_contact_form(
    contact: ContactInput,
    db: Session = Depends(get_db)
):

    # Store in database
    new_contact = Contact(
        name=contact.name,
        email=contact.email,
        message=contact.message
    )
    
    try:
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        
        
        return {
            "message": "Thank you for contacting us! We will get back to you soon.",
            "contact_id": new_contact.id,
            "status": "submitted"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing contact form: {str(e)}"
        )


@router.get("/submissions")
def get_contact_submissions(db: Session = Depends(get_db)):

    submissions = db.query(Contact).order_by(Contact.created_at.desc()).all()
    return {
        "total": len(submissions),
        "submissions": submissions
    }
