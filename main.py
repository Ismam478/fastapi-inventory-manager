from fastapi import FastAPI, Depends
from src.database_model import Product, ItemInput, BaseM, User, UserInput, UserLoginInput
from src.database import Session1, engine1
import src.database_model as db_model
from sqlalchemy.orm import Session
from src.authentication import hash_password, verify_password
from routers import users, products


db_model.BaseM.metadata.create_all(bind=engine1)


def get_db():
    db = Session1()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.get("/")
def welcome(db: Session = Depends(get_db)):
    return {"message": "Welcome to NEXORA!"}


app.include_router(users.router)
app.include_router(products.router)

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    db_products = db.query(Product).all()
    return db_products



    

