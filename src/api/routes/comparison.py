from __future__ import annotations

from fastapi import APIRouter

from src.config import get_settings
from src.api.schema import WorkspaceComparison
from src.tools.workspace_comparison import compare_reports,get_workspace_id
import requests

router = APIRouter()

@router.get("/comparison",response_model=WorkspaceComparison)
def comparison() -> WorkspaceComparison:
    settings = get_settings()
    dev_workspace_id = get_workspace_id(settings.DEV_WORKSPACE)
    prod_workspace_id = get_workspace_id(settings.PROD_WORKSPACE)
    return WorkspaceComparison(status=compare_reports(dev_workspace_id, prod_workspace_id))
