from fastapi import FastAPI, Depends, APIRouter, HTTPException
from src.database_model import Product, ItemInput, BaseM, User, UserInput, UserLoginInput
from src.database import Session1, engine1
from sqlalchemy.orm import Session
from src.authentication import hash_password, verify_password


router = APIRouter(
    prefix="/users",
    tags=["users"],
)

def get_db():
    db = Session1()
    try:
        yield db
    finally:
        db.close()


# User signup and login routes
@router.post("/signup")
def signup(user: UserInput, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        return {"message": "User already exists."}

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create new user
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully."}


@router.post("/login")
def login(user: UserLoginInput, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if not existing_user:
        return {"message": "Invalid username or password."}

    # Verify the password
    if verify_password(user.password, existing_user.password_hash):
        return {"message": "Login successful."}
    else:
        return {"message": "Invalid username or password."}