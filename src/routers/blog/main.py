# src/routers/blog/main.py
import json
import shutil
import requests
from . import models
from . import  schemas
from typing import List
from pathlib import Path
from datetime import datetime
from src.utils.db import get_db
from sqlalchemy.orm import Session
from src.routers.users.models import User
from src.utils.jwt import get_email_from_token
from fastapi import APIRouter, Depends, HTTPException, status, Request,Form,UploadFile,File

router = APIRouter(
    prefix="/api/blogs",
    tags=["Blogs"],
    responses={404: {"description": "Not found"}},
)

# @router.post("/create", response_model=schemas.BlogOut, status_code=201)
# def create_blog(blog: schemas.BlogCreate, request: Request, db: Session = Depends(get_db)):
#     """
#     Create a new blog post. Only admins can create.
#     """

#     # Authorization check
#     token = request.headers.get("Authorization")
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization token missing",
#         )
    
#     token = token.split(" ")[1]  # Assuming token is passed as "Bearer <token>"
#     email = get_email_from_token(token)

#     admin_user = db.query(User).filter(User.email == email).first()
#     if not admin_user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Admin user not found"
#         )
    
#     if admin_user.role != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You are not authorized to access this resource"
#         )

#     # Check if slug already exists
#     existing_blog = db.query(models.Blog).filter(models.Blog.slug == blog.slug).first()
#     if existing_blog:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Slug already exists. Please use a different slug."
#         )
    
#     new_blog = models.Blog(
#         title=blog.title,
#         description=blog.description,
#         slug=blog.slug,
#         publish_date=blog.publish_date if blog.publish_date else datetime.utcnow(),
#         categories=blog.categories,
#         body=blog.body,
#         status = True,
#     )
    
#     db.add(new_blog)
#     db.commit()
#     db.refresh(new_blog)
    
#     # Folder to save images
#     blog_folder = Path(f"public/blog/{new_blog.id}")
#     blog_folder.mkdir(parents=True, exist_ok=True)

#     # Process body content
#     updated_body = []
#     for block in blog.body:
#         block_data = block.dict()

#         if block_data.get("type") == "image":
#             image_url = block_data.get("url")
#             try:
#                 # Download image
#                 response = requests.get(image_url, stream=True)
#                 if response.status_code == 200:
#                     filename = image_url.split("/")[-1]  # Take filename from URL
#                     image_path = blog_folder / filename

#                     with open(image_path, "wb") as f:
#                         shutil.copyfileobj(response.raw, f)
                    
#                     # Update block to point to local server URL
#                     block_data["url"] = f"/public/blog/{new_blog.id}/{filename}"
#                 else:
#                     raise Exception("Failed to download image")
#             except Exception as e:
#                 print(f"Error downloading image: {e}")
#                 continue  # skip this image if any error

#         updated_body.append(block_data)

#     # Update blog body with new URLs
#     new_blog.body = updated_body
#     db.commit()

#     return new_blog



@router.post("/create", response_model=schemas.BlogOut, status_code=201)
def create_blog(request: Request,
    blog_data: str = Form(...), 
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    """
    Create a new blog post with optional image uploads.
    """

    # --- Authorization check ---
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )

    try:
        token = token.split(" ")[1]  # Bearer <token>
        email = get_email_from_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    admin_user = db.query(User).filter(User.email == email).first()
    if not admin_user or admin_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource"
        )

    # --- Parse blog data ---
    try:
        blog_dict = json.loads(blog_data)
        blog = schemas.BlogCreate(**blog_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid blog JSON: {e}")

    # --- Slug check ---
    existing_blog = db.query(models.Blog).filter(models.Blog.slug == blog.slug).first()
    if existing_blog:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists. Please use a different slug."
        )

    # --- Create blog entry ---
    new_blog = models.Blog(
        title=blog.title,
        description=blog.description,
        slug=blog.slug,
        publish_date=blog.publish_date if blog.publish_date else datetime.utcnow(),
        categories=blog.categories,
        body=[],  # temporary placeholder
        status=True,
    )

    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    # --- Image saving folder ---
    blog_folder = Path(f"public/blog/{new_blog.id}")
    blog_folder.mkdir(parents=True, exist_ok=True)

    # --- Process body content ---
    updated_body = []
    # Automatically assign names to uploaded images in the order received
    image_counter = 1  # Start numbering from 1

    for block in blog.body:
        if isinstance(block, dict):
            block_data = block
        else:
            block_data = block.dict()

        if block_data.get("type") == "image":
            if image_counter <= len(images):
                matched_file = images[image_counter - 1]
                filename = f"image{image_counter}{Path(matched_file.filename).suffix}"

                try:
                    image_path = blog_folder / filename
                    with open(image_path, "wb") as f:
                        shutil.copyfileobj(matched_file.file, f)

                    # Update the image URL in the block data
                    block_data["url"] = f"/public/blog/{new_blog.id}/{filename}"
                    image_counter += 1
                except Exception as e:
                    print(f"Error saving image: {e}")
                    continue
            else:
                print(f"Not enough uploaded images for block {image_counter}")
                continue

        updated_body.append(block_data)


    # --- Save updated body with local image URLs ---
    new_blog.body = updated_body
    db.commit()

    return new_blog


# ✅ Get a specific blog by blog ID
@router.get("/get_blog/{blog_id}", status_code=200)
def get_blog(blog_id: int, db: Session = Depends(get_db)):
    try:
        blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")

        # Update image URLs in body
        updated_body = []
        for block in blog.body:
            if isinstance(block, dict) and block.get("type") == "image" and "url" in block:
                relative_url = block["url"].lstrip("/")
                full_url = f"https://nutridietmitra.com/{relative_url}"
                block["url"] = full_url
            updated_body.append(block)

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
                "body": updated_body,
                "status": blog.status,
                "created_at": blog.created_at,
                "updated_at": blog.updated_at
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching blog: {str(e)}"
        )

#
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
            # Update image URLs in body
            updated_body = []
            for block in blog.body:
                if isinstance(block, dict) and block.get("type") == "image" and "url" in block:
                    relative_url = block["url"].lstrip("/")
                    full_url = f"https://nutridietmitra.com/{relative_url}"
                    block["url"] = full_url
                updated_body.append(block)

            blog_list.append({
                "id": blog.id,
                "title": blog.title,
                "description": blog.description,
                "slug": blog.slug,
                "publish_date": blog.publish_date,
                "categories": blog.categories,
                "body": updated_body,
                "status": blog.status,
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

# Public endpoint to fetch blog by slug
@router.get("/slug/{slug}")
def get_blog_by_slug(slug: str, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog