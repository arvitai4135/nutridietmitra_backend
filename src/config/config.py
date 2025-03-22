# src/config.py
import os

APPNAME = "Nutridiet"
VERSION = "v1"
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token expiry time in minutes