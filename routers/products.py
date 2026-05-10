from fastapi import APIRouter, Depends, HTTPException
from src.database_model import Product, ItemInput, BaseM, User, UserInput, UserLoginInput
from src.database import Session1, engine1
from sqlalchemy.orm import Session
router = APIRouter(
    prefix="/products",
    tags=["products"],
)


def get_db():
    db = Session1()
    try:
        yield db
    finally:
        db.close()



# Admin routes for adding, deleting, and updating products
@router.post("/admin/products/add_products")
def add_products(item: ItemInput, db: Session = Depends(get_db)):
    db.add(Product(**item.model_dump()))
    db.commit()
    return {"message": f"Product added successfully!"}



@router.delete("/admin/products/delete_products")
def delete_products(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
        return {"message": f"Product with id {product_id} deleted successfully!"}
    else:
        return {"message": f"Product with id {product_id} not found."}
    

@router.put("/admin/products/update_products")
def update_products(product_id: int, item: ItemInput, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.name = item.name
        product.price = item.price
        product.description = item.description
        product.quantity = item.quantity
        product.in_stock = item.in_stock
        db.commit()
        return {"message": f"Product with id {product_id} updated successfully!"}
    else:
        return {"message": f"Product with id {product_id} not found."}