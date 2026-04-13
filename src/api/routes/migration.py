from __future__ import annotations

from fastapi import APIRouter

from src.config import get_settings
from src.tools.export_pbix import export_report
from src.tools.workspace import get_workspace_id
from src.tools.auth import get_auth_headers
from src.tools.upload_pbix import upload_pbix, check_import_status, delete_file
from src.api.schema import ExportResponse

import requests

router = APIRouter()

@router.get("/migration",response_model=ExportResponse)
def migration(dashboard_name: str, from_workspace_name: str, to_workspace_name: str) -> str:
    settings = get_settings()
    export_info=export_report(dashboard_name, from_workspace_name)
    headers = get_auth_headers()
    workspace_id = get_workspace_id(to_workspace_name, headers)
    import_id = upload_pbix(workspace_id,
                            export_info["file_path"],
                            dashboard_name,
                            headers) 
    response=check_import_status(workspace_id, import_id, headers)
    delete_file(export_info["file_path"])
    return ExportResponse( dataset_id=response["dataset_id"], report_id=response["report_id"],status=response["status"])