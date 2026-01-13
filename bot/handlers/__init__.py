"""
Handlers package
"""

from .start import router as start_router
from .complaint_create import router as complaint_create_router
from .complaint_view import router as complaint_view_router
from .admin import router as admin_router

__all__ = [
    'start_router',
    'complaint_create_router',
    'complaint_view_router',
    'admin_router'
]