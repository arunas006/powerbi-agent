from __future__ import annotations
from src.config import get_settings
import requests
from src.tools.auth import get_auth_headers
from typing import Optional
from src.tools.workspace import get_workspace_id

settings = get_settings()

def get_reports(workspace_id: str, headers: Optional[dict] = None) -> list:

    """
    This function retrieves the reports for a given workspace ID using the Power BI API.
    """
    url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/reports"
    if not headers:
        headers = get_auth_headers()

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json().get("value", [])
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to retrieve reports: {e}")
    
def compare_reports(dev_workspace_id: str, prod_workspace_id: str):
    """
    This function compares the reports in the development and production workspaces and prints the differences.
    """
    
    dev_reports = get_reports(dev_workspace_id)
    prod_reports = get_reports(prod_workspace_id)

    dev_report_names = {report["name"] for report in dev_reports}
    prod_report_names = {report["name"] for report in prod_reports}

    missing_in_prod = dev_report_names - prod_report_names
    missing_in_dev = prod_report_names - dev_report_names

    return {
        "missing_in_prod": missing_in_prod,
        "missing_in_dev": missing_in_dev,
        "counts": {
            "dev_total": len(dev_report_names),
            "prod_total": len(prod_report_names),
            "missing_in_prod": len(missing_in_prod),
            "missing_in_dev": len(missing_in_dev),
        },
    }

if __name__ == "__main__":
    dev_workspace_id = get_workspace_id(settings.DEV_WORKSPACE)
    prod_workspace_id = get_workspace_id(settings.PROD_WORKSPACE)

    if not dev_workspace_id or not prod_workspace_id:
        print("❌ Could not retrieve workspace IDs. Please check your configuration.")
    else:
        comparison_result = compare_reports(dev_workspace_id, prod_workspace_id)
        print("Report Comparison Result:")
        print(comparison_result)