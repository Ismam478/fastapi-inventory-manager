from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Path as PathParam
from src.database_model import Product, ItemInput, BaseM, Review, ReviewInput, ReviewResponse, ProductImage, ProductImageResponse
from src.database import Session1, engine1
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import aiofiles
from pathlib import Path
import uuid

from src.user_access import require_roles

allow_admin_only = require_roles(["admin"])

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(allow_admin_only)]
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
    db: Session = Depends(get_db),
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


@router.delete("/delete_products/{product_id}")
def delete_products(product_id: int = PathParam(...), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found.")
    
    # Delete associated reviews
    db.query(Review).filter(Review.product_id == product_id).delete()
    db.delete(product)
    db.commit()
    return {"message": f"Product with id {product_id} deleted successfully!"}
    

@router.put("/update_products/{product_id}")
def update_products(product_id: int = PathParam(...), item: ItemInput = None, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found.")
    
    product.name = item.name
    product.price = item.price
    product.description = item.description
    product.quantity = item.quantity
    # product.in_stock = item.in_stock
    # if item.image_url is not None:
    #     product.image_url = item.image_url
    db.commit()
    return {"message": f"Product with id {product_id} updated successfully!"}


# ============ IMAGE UPLOAD ENDPOINT ============

@router.post("/upload-image/{product_id}")
async def upload_product_image(
    product_id: int = PathParam(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
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
    
    # Generate unique filename with UUID to avoid conflicts
    unique_filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    try:
        contents = await file.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(contents)
        
        # Get the next upload order number
        last_image = db.query(ProductImage).filter(ProductImage.product_id == product_id).order_by(ProductImage.upload_order.desc()).first()
        next_order = (last_image.upload_order + 1) if last_image else 0
        
        # Save to database
        image_url = f"/static/uploads/{unique_filename}"
        product_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            upload_order=next_order
        )
        db.add(product_image)
        db.commit()
        db.refresh(product_image)
        
        return {
            "message": "Image uploaded successfully",
            "filename": unique_filename,
            "image_url": image_url,
            "upload_order": next_order
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")