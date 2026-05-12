from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from src.database_model import Product, ItemInput, BaseM, User, UserInput, UserLoginInput
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
def get_products(db: Session = Depends(get_db)):
    """Get all products"""
    html_path = Path("src/products.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return db.query(Product).all()

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
        return db_product
    else:
        raise HTTPException(status_code=404, detail="Product not found")

