# src/routers/blog/main.py
from . import models
from . import  schemas
from datetime import datetime
from src.utils.db import get_db
from sqlalchemy.orm import Session
from src.routers.users.models import User
from src.utils.jwt import get_email_from_token
from fastapi import APIRouter, Depends, HTTPException, status, Request

router = APIRouter(
    prefix="/api/blogs",
    tags=["Blogs"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create", response_model=schemas.BlogOut, status_code=201)
def create_blog(blog: schemas.BlogCreate, request: Request, db: Session = Depends(get_db)):
    """
    Create a new blog post. Only admins can create.
    """

    # Authorization check
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )
    
    token = token.split(" ")[1]  # Assuming token is passed as "Bearer <token>"
    email = get_email_from_token(token)

    admin_user = db.query(User).filter(User.email == email).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    if admin_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource"
        )

    # Check if slug already exists
    existing_blog = db.query(models.Blog).filter(models.Blog.slug == blog.slug).first()
    if existing_blog:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists. Please use a different slug."
        )
    
    new_blog = models.Blog(
        title=blog.title,
        description=blog.description,
        slug=blog.slug,
        publish_date=blog.publish_date if blog.publish_date else datetime.utcnow(),
        categories=blog.categories,
        body=blog.body,
        status = True,
    )
    
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return new_blog

# ✅ Get a specific blog by blog ID
@router.get("/get_blog/{blog_id}", status_code=200)
def get_blog(blog_id: int, db: Session = Depends(get_db)):
    try:
        blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        return {
            "success": True,
            "status": 200,
            "message": "Blog fetched successfully",
            "data": {
                "id": blog.id,
                "title": blog.title,
                "description": blog.description,
                "slug": blog.slug,
                "publish_date": blog.publish_date,
                "categories": blog.categories,
                "body": blog.body,
                "status":blog.status,
                "created_at": blog.created_at,
                "updated_at": blog.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching blog: {str(e)}"
        )

# ✅ Get all blogs
@router.get("/all_blog_lists", status_code=200)
def get_all_blogs(db: Session = Depends(get_db)):
    try:
        blogs = db.query(models.Blog).order_by(models.Blog.publish_date.desc()).all()
        if not blogs:
            return {
                "success": True,
                "status": 200,
                "message": "No blogs found",
                "data": []
            }

        blog_list = []
        for blog in blogs:
            blog_list.append({
                "id": blog.id,
                "title": blog.title,
                "description": blog.description,
                "slug": blog.slug,
                "publish_date": blog.publish_date,
                "categories": blog.categories,
                "body": blog.body,
                "status":blog.status,
                "created_at": blog.created_at,
                "updated_at": blog.updated_at
            })

        return {
            "success": True,
            "status": 200,
            "message": "Blogs fetched successfully",
            "data": blog_list
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching blogs: {str(e)}"
        )
        
@router.delete("/delete/{blog_id}", status_code=200)
def delete_blog(blog_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Soft delete a blog post by setting its status to False. Only admins can delete.
    """

    # Authorization check
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )
    
    token = token.split(" ")[1]  # Assuming "Bearer <token>"
    email = get_email_from_token(token)

    admin_user = db.query(User).filter(User.email == email).first()
    if not admin_user or admin_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource"
        )

    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog not found"
        )

    # Soft delete: mark as inactive
    blog.status = False
    db.commit()
    

    return {
            "success": True,
            "status": 200,
            "message": "Blog deleted successfully.",
        }
    
@router.put("/update/{blog_id}", response_model=schemas.BlogOut)
def update_blog(blog_id: int, blog_update: schemas.BlogCreate, request: Request, db: Session = Depends(get_db)):
    """
    Update a blog post. Only admins can update.
    """

    # Authorization check
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )
    
    token = token.split(" ")[1]
    email = get_email_from_token(token)

    admin_user = db.query(User).filter(User.email == email).first()
    if not admin_user or admin_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource"
        )

    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog not found"
        )

    # Update blog fields
    blog.title = blog_update.title
    blog.description = blog_update.description
    blog.slug = blog_update.slug
    blog.publish_date = blog_update.publish_date if blog_update.publish_date else blog.publish_date
    blog.categories = blog_update.categories
    blog.body = blog_update.body

    db.commit()
    db.refresh(blog)

    return blog
