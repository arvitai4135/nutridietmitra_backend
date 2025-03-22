# src/routers/__init__.py
from .users.main import router as users_router
from .feedback.main import router as feedback_router
from .dashboard.main import  router as dashboard_route
from .appoitment.main import router as appoitment_router


__all__ = [
    "users_router",
    "feedback_router",
    "dashboard_route",
    "appoitment_router"
           ]
