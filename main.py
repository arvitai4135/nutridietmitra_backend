import uvicorn
from fastapi import FastAPI, Request
from src.config import APPNAME, VERSION
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from src.routers import (users_router, 
                         feedback_router,
                         dashboard_route, 
                         appoitment_router, 
                         admin_router, 
                         payment_router,
                         blog_router)

# Defining the application
app = FastAPI(
    title=APPNAME,
    version=VERSION,
)

# Define allowed origins
origins = [
    "http://localhost:5173",    # Frontend during development
    "http://127.0.0.1:5173",    # Alternate localhost
    "http://localhost:3001",    # Frontend during development
    "http://127.0.0.1:3001",
    "http://207.180.251.252:3001", # Alternate localhost
    "https://nutridietmitra.com",  # Production domain
]


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Including all the routes for the 'users' module
app.include_router(users_router)
app.include_router(feedback_router)
app.include_router(appoitment_router)
app.include_router(admin_router)
app.include_router(payment_router)
app.include_router(blog_router)

@app.get("/")
def main_function():
    """
    Redirect to documentation (`/docs/`).
    """
    return RedirectResponse(url="/docs/")



@app.post("/token")
def forward_to_login():
    """
    Redirect to token-generation (`/auth/token`). Used to make Auth in Swagger-UI work.
    """
    return RedirectResponse(url="/token")

app.mount("/public", StaticFiles(directory="public"), name="public")


# @app.get("/api")
# async def read_root():
#     return {"message": "Hello from API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
