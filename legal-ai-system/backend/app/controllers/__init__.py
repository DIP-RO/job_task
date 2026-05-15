from .document_controller import router as document_router
from .draft_controller import router as draft_router
from .edit_controller import router as edit_router

__all__ = ["document_router", "draft_router", "edit_router"]
