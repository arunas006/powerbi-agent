from __future__ import annotations

from fastapi import APIRouter

from src.config import get_settings
from src.tools.auth import health_check
from src.api.schema import HealthResponse
import requests

router = APIRouter()

@router.get("/health",response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status=health_check())



