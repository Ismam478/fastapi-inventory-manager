from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, JSON, Boolean
from pydantic import BaseModel, validator


BaseM = declarative_base()


class Product(BaseM):
    __tablename__ = "products"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(100), nullable=False)
    price: float = Column(Float, nullable=False)
    description: str = Column(Text)
    quantity: int = Column(Integer, nullable=False)
    in_stock: bool = Column(Boolean, nullable=False)
    # free_delivery: bool = Column(Boolean, nullable=False)
    # picture_url: list[str] = Column(String(255))


class ItemInput(BaseModel):
    id : int
    name : str
    price : float
    description : str
    quantity : int
    in_stock : bool
    # picture_url : list[str]
    
    @validator('in_stock', pre=False, always=True)
    def set_in_stock_from_quantity(cls, v, values):
        if 'quantity' in values:
            return values['quantity'] > 0
        return v
    

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