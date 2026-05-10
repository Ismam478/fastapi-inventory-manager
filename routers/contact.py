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
    """
    Submit a contact form message.
    In production, you would send an email here.
    For now, we store it in the database.
    """
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
        
        # TODO: Send email notification to admin
        # send_email_to_admin(contact)
        
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
    """
    Get all contact form submissions (admin only - in production, add auth).
    """
    submissions = db.query(Contact).order_by(Contact.created_at.desc()).all()
    return {
        "total": len(submissions),
        "submissions": submissions
    }


# Optional: Email sending function (requires additional setup)
"""
Example for sending emails using FastAPI-Mail:

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    mail_username=os.getenv("MAIL_USERNAME"),
    mail_password=os.getenv("MAIL_PASSWORD"),
    mail_from=os.getenv("MAIL_FROM"),
    mail_port=int(os.getenv("MAIL_PORT", 587)),
    mail_server=os.getenv("MAIL_SERVER"),
    mail_starttls=True,
    mail_ssl_tls=False,
)

async def send_email_to_admin(contact: ContactInput):
    message = MessageSchema(
        subject=f"New Contact Form Submission from {contact.name}",
        recipients=[os.getenv("ADMIN_EMAIL")],
        body=f"Name: {contact.name}\\nEmail: {contact.email}\\nMessage: {contact.message}",
        simple=True,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
"""
