# src/schemas/blog.py

from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class BlogCreate(BaseModel):
    title: str
    description: Optional[str]
    slug: str
    publish_date: Optional[datetime]
    categories: Optional[List[str]]
    body: List[Any]  # body is a list of structured objects (paragraphs, headings, etc.)

class BlogOut(BlogCreate):
    id: int

    class Config:
        orm_mode = True
