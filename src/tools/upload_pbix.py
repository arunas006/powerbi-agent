from __future__ import annotations
from src.config import get_settings
import requests
from src.tools.auth import get_auth_headers
from src.tools.workspace import get_workspace_id
from src.tools.export_pbix import report_details
import os
import time

settings = get_settings()

def upload_pbix(workspace_id : str,
                file_path: str,
                dataset_name: str,
                headers: dict) -> str | None:
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    headers = get_auth_headers()

    url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/imports?datasetDisplayName={dataset_name}&nameConflict=CreateOrOverwrite"


    filename = os.path.basename(file_path)

    headers.pop("Content-Type", None)

    with open(file_path, "rb") as f:
        files = {
            'file': (filename, f, 'application/octet-stream')
        }

        res = requests.post(url, headers=headers, files=files)

    if res.status_code not in [200, 202]:
        raise Exception(f"Upload failed: {res.text}")
    
    response = res.json()
    import_id = response["id"]

    if import_id is None:
        raise Exception("Import ID not found in response")
    
    return import_id

def check_import_status(workspace_id: str,
                        import_id: str,
                        headers: dict,
                        timeout=300,
                        interval=5):
    
    headers = get_auth_headers()

    url = f"{settings.POWER_BI_BASE_URL}/groups/{workspace_id}/imports/{import_id}"

    start_time = time.time()
    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            raise Exception(f"Failed to check import status: {res.text}")

        data = res.json()
        status = data.get("importState")

       

        if status == "Succeeded":   # ✅ FIXED
            dataset_id = data["datasets"][0]["id"]
            report_id = data["reports"][0]["id"]
            return {"dataset_id": dataset_id, "report_id": report_id, "status":"Sucess"}

        elif status in ["Failed", "Cancelled"]:
            raise Exception(f"Import failed: {data}")

        time.sleep(interval)
        attempts += 1

    raise TimeoutError(f"Import did not complete within {timeout} seconds")

def delete_file(file_path):
    try:
        os.remove(file_path)
        
    except Exception as e:
        raise Exception(f"Failed to delete temporary file: {e}")

if __name__ == "__main__":
    headers = get_auth_headers()
    workspace_id = get_workspace_id("Prod", headers)

    file_path = r"C:\dev\powerbi\temp\invoice-Dashboard.pbix"
    dataset_name = "invoice-Dashboard"

    import_id = upload_pbix(workspace_id, file_path, dataset_name, headers)
    dataset_id, report_id = check_import_status(workspace_id, import_id, headers)
    delete_file(file_path)

    print("Dataset ID:", dataset_id)
    print("Report ID:", report_id)

    
