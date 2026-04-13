from __future__ import annotations
from src.config import get_settings
import requests
from src.tools.auth import get_auth_headers
from src.tools.workspace import get_workspace_id
from src.tools.export_pbix import report_details
import os

settings = get_settings()

# def delete_report(workspace_id, report_id, headers):

#     """Deletes a Power BI report."""

#     url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/reports/{report_id}"

#     headers.pop("Content-Type", None)
    
#     res = requests.delete(url, headers=headers)
       
#     if res.status_code == 404:
#         raise Exception(f"Report {report_id} not found")
    
#     if res.status_code not in [200, 202, 204]:
#         raise Exception(f"Failed to delete report {report_id}: {res.text}")
    
#     return {
#         "status":"success",
#         "message":"Report deleted successfully",
#         "resource_id":report_id
#     }

# def delete_dataset(workspace_id, dataset_id, headers):

#     """Deletes a Power BI dataset."""
#     url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}"

#     headers.pop("Content-Type", None)
    
#     res = requests.delete(url, headers=headers)

#     if res.status_code == 404:
#         raise Exception(f"Dataset {dataset_id} not found")
    
#     if res.status_code not in [200, 202, 204]:
#         raise Exception(f"Failed to delete report {dataset_id}: {res.text}")
    
#     return {
#         "status":"success",
#         "message":"Dataset deleted successfully",
#         "resource_id":dataset_id
#     }

def delete_report_and_dataset(workspace_id: str, report_id: str, dataset_id: str, headers: dict):
    """
    Deletes both report and dataset in correct order.
    """

    headers.pop("Content-Type", None)

    results = {}

    # Step 1: Delete Report
    report_url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/reports/{report_id}"
    report_res = requests.delete(report_url, headers=headers)

    if report_res.status_code == 404:
        results["report"] = f"Report {report_id} not found"
    elif report_res.status_code not in [200, 202, 204]:
        raise Exception(f"Failed to delete report {report_id}: {report_res.text}")
    else:
        results["report"] = "Deleted successfully"

    # Step 2: Delete Dataset
    dataset_url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}"
    dataset_res = requests.delete(dataset_url, headers=headers)

    if dataset_res.status_code == 404:
        results["dataset"] = f"Dataset {dataset_id} not found"
    elif dataset_res.status_code not in [200, 202, 204]:
        raise Exception(f"Failed to delete dataset {dataset_id}: {dataset_res.text}")
    else:
        results["dataset"] = "Deleted successfully"

    return {
        "status": "success",
        "message": "Delete operation completed",
        "details": results
    }

if __name__ == "__main__":
    headers = get_auth_headers()
    workspace_id = get_workspace_id("Prod", headers)

    data = report_details("invoice-Dashboard", "Prod")
  
    # delete_report(workspace_id, data['report_id'], headers)
    # delete_dataset(workspace_id, data['dataset_id'], headers)