from __future__ import annotations
from fastapi import APIRouter

from src.config import get_settings
from openai import OpenAI
from src.tools.recommended_dashboard import recommend_dashboard
from src.api.schema import DashboardResponse
import requests

router = APIRouter()

@router.get("/recommend",response_model=DashboardResponse)
def Search_Dashboard(user_query: str, top_n: int) -> DashboardResponse:
    settings = get_settings()
    response = recommend_dashboard(user_query, top_n)
    return response
   