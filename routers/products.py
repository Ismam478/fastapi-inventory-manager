from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from src.database_model import Product, ItemInput, BaseM, Review, ReviewInput, ReviewResponse
from src.database import Session1, engine1
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import aiofiles
from pathlib import Path

router = APIRouter(
    prefix="/products",
    tags=["products"],
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


@router.post("/admin/products/add_products")
def add_products(item: ItemInput, db: Session = Depends(get_db)):
    db.add(Product(**item.model_dump()))
    db.commit()
    return {"message": f"Product added successfully!"}


@router.delete("/admin/products/delete_products")
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


# ============ IMAGE UPLOAD ENDPOINT ============

@router.post("/admin/upload-image")
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


# ============ REVIEW ENDPOINTS ============

@router.post("/{product_id}/reviews")
def add_review(
    product_id: int,
    review: ReviewInput,
    user_id: int = Query(...),  # In production, get from JWT token
    db: Session = Depends(get_db)
):
    """Add a review to a product"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create new review
    new_review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return {
        "message": "Review added successfully",
        "review": ReviewResponse.from_orm(new_review)
    }


@router.get("/{product_id}/reviews")
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get all reviews for a product with average rating"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating_result = db.query(func.avg(Review.rating)).filter(
        Review.product_id == product_id
    ).scalar()
    avg_rating = float(avg_rating_result) if avg_rating_result else 0
    
    return {
        "product_id": product_id,
        "total_reviews": len(reviews),
        "average_rating": round(avg_rating, 1),
        "reviews": [ReviewResponse.from_orm(r) for r in reviews]
    }


@router.delete("/{product_id}/reviews/{review_id}")
def delete_review(
    product_id: int,
    review_id: int,
    db: Session = Depends(get_db)
):
    """Delete a review (optional - in production, verify ownership)"""
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.product_id == product_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db.delete(review)
    db.commit()
    
    return {"message": "Review deleted successfully"}