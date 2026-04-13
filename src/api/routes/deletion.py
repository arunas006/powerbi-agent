from __future__ import annotations

from fastapi import APIRouter
from src.config import get_settings
from src.api.schema import DeleteResponse
from src.tools.delete_pbix import delete_report_and_dataset
from src.tools.auth import get_auth_headers
from src.tools.workspace import get_workspace_id
from src.tools.export_pbix import report_details
import requests

router = APIRouter()

@router.get("/deletion",response_model=DeleteResponse)
def deletion(dashboard_name: str, workspace_name: str) -> DeleteResponse:
    settings = get_settings()
    headers = get_auth_headers()
    workspace_id = get_workspace_id(workspace_name, headers)
    data = report_details(dashboard_name, workspace_name)
    delete_report_and_dataset(workspace_id, data['report_id'], data['dataset_id'], headers)

    return DeleteResponse(status="success", message="Report and dataset deleted successfully", resource_id=data['report_id'], Dashboard_name=dashboard_name)