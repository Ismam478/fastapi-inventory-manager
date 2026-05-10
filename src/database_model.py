from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, JSON, Boolean, DateTime, ForeignKey
from pydantic import BaseModel, validator
from datetime import datetime


BaseM = declarative_base()


class Product(BaseM):
    __tablename__ = "products"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(100), nullable=False)
    price: float = Column(Float, nullable=False)
    description: str = Column(Text)
    quantity: int = Column(Integer, nullable=False)
    in_stock: bool = Column(Boolean, nullable=False)
    image_url: str = Column(String(500), nullable=True)


class Review(BaseM):
    __tablename__ = "reviews"

    id: int = Column(Integer, primary_key=True)
    product_id: int = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating: int = Column(Integer, nullable=False)  # 1-5 stars
    comment: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


class Contact(BaseM):
    __tablename__ = "contacts"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(100), nullable=False)
    email: str = Column(String(100), nullable=False)
    message: str = Column(Text, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


class ItemInput(BaseModel):
    id : int
    name : str
    price : float
    description : str
    quantity : int
    in_stock : bool
    
    @validator('in_stock', pre=False, always=True)
    def set_in_stock_from_quantity(cls, v, values):
        if 'quantity' in values:
            return values['quantity'] > 0
        return v


class ReviewInput(BaseModel):
    rating: int
    comment: str
    
    @validator('rating')
    def rating_range(cls, v):
        if not (1 <= v <= 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class ContactInput(BaseModel):
    name: str
    email: str
    message: str


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True


class User(BaseM):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True)
    username: str = Column(String(50), unique=True, nullable=False)
    email: str = Column(String(100), unique=True, nullable=False)
    password_hash: str = Column(String(255), nullable=False)


class UserInput(BaseModel):
    username: str
    email: str
    password: str

class UserLoginInput(BaseModel):
    username: str
    password: str