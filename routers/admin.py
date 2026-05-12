from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from src.database_model import Product, ItemInput, BaseM, Review, ReviewInput, ReviewResponse
from src.database import Session1, engine1
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import aiofiles
from pathlib import Path

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

UPLOAD_DIR = "static/uploads"

# Ensure upload directory exists
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def get_db():
    db = Session1()
    try:
        yield db
    finally:
        db.close()


# ============ PRODUCT ENDPOINTS ============

@router.get("/")
def list_products(
    search: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    in_stock: bool = Query(None),
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering and search"""
    query = db.query(Product)
    
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") | 
            Product.description.ilike(f"%{search}%")
        )
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if in_stock is not None:
        query = query.filter(Product.in_stock == in_stock)
    
    products = query.all()
    
    return {
        "total": len(products),
        "products": products
    }


@router.post("/add_products")
def add_products(item: ItemInput, db: Session = Depends(get_db)):
    new_product = Product(**item.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Product added successfully!", "product": new_product}


@router.delete("/delete_products")
def delete_products(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        # Delete associated reviews
        db.query(Review).filter(Review.product_id == product_id).delete()
        db.delete(product)
        db.commit()
        return {"message": f"Product with id {product_id} deleted successfully!"}
    else:
        return {"message": f"Product with id {product_id} not found."}
    

@router.put("/update_products")
def update_products(product_id: int, item: ItemInput, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.name = item.name
        product.price = item.price
        product.description = item.description
        product.quantity = item.quantity
        # product.in_stock = item.in_stock
        # if item.image_url is not None:
        #     product.image_url = item.image_url
        db.commit()
        return {"message": f"Product with id {product_id} updated successfully!"}
    else:
        return {"message": f"Product with id {product_id} not found."}


# ============ IMAGE UPLOAD ENDPOINT ============

@router.post("/upload-image")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image for a product"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate file type
    allowed_extensions = {"jpg", "jpeg", "png", "gif", "webp"}
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {allowed_extensions}"
        )
    
    # Generate unique filename
    filename = f"product_{product_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    try:
        contents = await file.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(contents)
        
        # Update product with image URL
        image_url = f"/static/uploads/{filename}"
        product.image_url = image_url
        db.commit()
        
        return {
            "message": "Image uploaded successfully",
            "filename": filename,
            "image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")