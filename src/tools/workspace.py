from __future__ import annotations
from src.config import get_settings
from typing import Optional
from src.tools.auth import get_auth_headers
import requests

settings = get_settings()

def get_workspace_id(workspace_name, headers: Optional[dict] = None) -> str | None:
    """
    This function retrieves the workspace ID for a given workspace name using the Power BI API.
    """

    url = f"{settings.POWER_BI_BASE_URL}/groups"
    if not headers:
        headers = get_auth_headers()

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        workspaces = res.json().get("value", [])

        for ws in workspaces:
            if ws["name"] == workspace_name:
                return ws["id"]

        return None
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to retrieve workspace ID: {e}")

if __name__ == "__main__":
    dev_workspace_id = get_workspace_id(settings.DEV_WORKSPACE)
    prod_workspace_id = get_workspace_id(settings.PROD_WORKSPACE)

    print(f"Dev Workspace ID: {dev_workspace_id}")
    print(f"Prod Workspace ID: {prod_workspace_id}")



