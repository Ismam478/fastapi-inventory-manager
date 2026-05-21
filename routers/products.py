from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from src.database_model import Product, ItemInput, BaseM, Review, ReviewInput, ReviewResponse, ProductResponse, ProductImage, ProductImageResponse
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
    
    # Add images to each product
    product_responses = []
    for p in products:
        product_resp = ProductResponse.model_validate(p)
        images = db.query(ProductImage).filter(ProductImage.product_id == p.id).order_by(ProductImage.upload_order).all()
        product_resp.images = [ProductImageResponse.model_validate(img) for img in images]
        # Set image_url to the first image if available
        if images:
            product_resp.image_url = images[0].image_url
        product_responses.append(product_resp)
    
    return {
        "total": len(product_responses),
        "products": product_responses
    }


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