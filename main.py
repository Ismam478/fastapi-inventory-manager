from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from src.database_model import Product, ItemInput, BaseM, User, UserInput, UserLoginInput, ProductResponse, ProductImage, ProductImageResponse
from src.database import Session1, engine1
import src.database_model as db_model
from sqlalchemy.orm import Session
from src.authentication import hash_password, verify_password
from routers import users, products, contact, admin
from pathlib import Path


# Create tables for new models
db_model.BaseM.metadata.create_all(bind=engine1)


def get_db():
    db = Session1()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(
    title="NEXORA Inventory API",
    description="Modern inventory management system API",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for image uploads
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Redirect to home page"""
    return RedirectResponse(url="/home")


@app.get("/home")
def home():
    """Serve the frontend HTML"""
    html_path = Path("src/homepage.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"error": "Frontend not found"}


@app.get("/products")
def products_page():
    """Serve the products page"""
    html_path = Path("src/products.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"error": "Products page not found"}


@app.get("/signup")
def signup_page():
    """Serve the signup page"""
    html_path = Path("src/signup.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"error": "Signup page not found"}

@app.get("/login")
def login_page():
    """Serve the login page"""
    html_path = Path("src/login.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"error": "Login page not found"}

@app.get("/admin")
def admin_page():
    """Serve the admin dashboard"""
    html_path = Path("src/admin.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"error": "Admin page not found"}

@app.get("/api/status")
def api_status(db: Session = Depends(get_db)):
    """Check API status"""
    return {
        "status": "online",
        "message": "NEXORA API is running",
        "endpoints": [
            "/home - Frontend",
            "/products/ - Get all products",
            "/docs - API Documentation"
        ]
    }


# Include routers
app.include_router(users.router)
app.include_router(products.router)
app.include_router(contact.router)
app.include_router(admin.router)


@app.get("/products/{product_id}")
def get_products(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        product_resp = ProductResponse.model_validate(db_product)
        # Add images
        images = db.query(ProductImage).filter(ProductImage.product_id == product_id).order_by(ProductImage.upload_order).all()
        product_resp.images = [ProductImageResponse.model_validate(img) for img in images]
        if images:
            product_resp.image_url = images[0].image_url
        return product_resp
    else:
        raise HTTPException(status_code=404, detail="Product not found")

