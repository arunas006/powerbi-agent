
from __future__ import annotations
from src.config import get_settings
import requests
from src.tools.workspace import get_workspace_id
from src.tools.auth import get_auth_headers
import os

settings = get_settings()

def report_details(report_name:str, workrpace:str):

    """Extracts report details from the API response based on the report name."""

    headers = get_auth_headers()

    workspace_id = get_workspace_id(workrpace, headers)

    url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/reports"

    response = requests.get(url, headers=headers)
    data = response.json()
    # return data

    for report in data['value']:
        if report.get('name',"").strip().lower() == report_name.strip().lower():
            return {
                "report_id": report["id"],
                "dataset_id": report["datasetId"],
                "report_name": report["name"]
            }
    return None

def generate_file_path(temp_dir, report_name):
    """Generates a sanitized file path for the exported PBIX file."""
    import re
    # Remove special characters and spaces from the report name
    sanitized_report_name = re.sub(r'[^a-zA-Z0-9_-]', '_', report_name)
    file_path = f"{temp_dir}/{sanitized_report_name}.pbix"
    return file_path
        
def clean_input(value: str) -> str:
    return value.strip().strip('"').strip("'")

def get_report_info(report_name:str, workspace_name:str):

    """Fetches report information for a given report name and workspace."""
   

    # headers = get_auth_headers()
    # workspace_id = get_workspace_id(workspace_name, headers)
    # url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/reports"
    try:
        # response = requests.get(url, headers=headers)
        # response.raise_for_status()
        # data = response.json()
        report_info = report_details(report_name, workspace_name)
        

        if not report_info:
            raise Exception(f"Report '{report_name}' not found in workspace '{workspace_name}'.")   
        
        return report_info
    
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch report details: {e}")
 



def export_pbix(workspace_id, report_id, report_name,headers):

    """Exports a Power BI report as a PBIX file and saves it to a temporary directory."""

    settings = get_settings()

    url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/reports/{report_id}/Export"

    res = requests.get(url, headers=headers, stream=True)
    

    TEMP_DIR = settings.TEMP_DIR
    os.makedirs(TEMP_DIR, exist_ok=True)

    file_path = generate_file_path(TEMP_DIR, report_name)

    if res.status_code != 200:
        raise Exception(f"Failed to export report: {res.status_code} - {res.text}")

    with open(file_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)

    return file_path

def export_report(report_name:str, workspace_name:str):
    """Main function to export a report given its name and workspace."""

    report_name = clean_input(report_name)
    workspace_name = clean_input(workspace_name)
    print("RAW INPUT report_name:", report_name)
    print("RAW INPUT workspace_name:", workspace_name)

    headers = get_auth_headers()

    workspace_id = get_workspace_id(workspace_name, headers)

    report_info = get_report_info(report_name, workspace_name)

    if not report_info:
        raise Exception(f"Report '{report_name}' not found in workspace '{workspace_name}'.")
    
    file_path = export_pbix(workspace_id, report_info['report_id'], report_info['report_name'], headers)

    return {
        "report_name": report_info['report_name'],
        "report_id": report_info['report_id'],
        "dataset_id": report_info['dataset_id'],
        "file_path": file_path
    }

if __name__ == "__main__":
    report_name = "invoice-Dashboard"
    workspace_name = "Dev"

    # data=report_details(report_name, workspace_name)
    # print(data)
    export_report(report_name, workspace_name)