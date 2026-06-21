"""Authentication service initialization for FlowPilot AI."""

from fastapi import APIRouter
from src.services.auth.routes import router as auth_router


def include_auth_routers(main_router: APIRouter) -> None:
    """Include all auth routers in the main API router."""
    
    main_router.include_router(auth_router)
