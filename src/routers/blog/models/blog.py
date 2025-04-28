# src/models/blog.py
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, ARRAY,Boolean


Base = declarative_base()

class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String, unique=True, nullable=False)
    publish_date = Column(DateTime, default=datetime.utcnow)
    categories = Column(ARRAY(String), nullable=True)
    body = Column(JSONB, nullable=False)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
