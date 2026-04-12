"""
Health check endpoint.
"""
from fastapi import APIRouter

from app.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for the Pre-Flight Validation API."""
    return HealthResponse(
        status="healthy",
        service="preflight-validator",
        version="1.0.0",
    )
