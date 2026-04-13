import requests
from dotenv import load_dotenv
import os
load_dotenv()
from datetime import datetime
import time

tenant_id = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://analysis.windows.net/powerbi/api/.default",
    "grant_type": "client_credentials"
}

res = requests.post(url, data=data)
token = res.json().get("access_token")
# print(token)


# To see what are the workspaces available in the tenant.
headers = {
    "Authorization": f"Bearer {token}"
}

url = "https://api.powerbi.com/v1.0/myorg/groups"

res = requests.get(url, headers=headers)

workspaces = res.json()["value"]
print(workspaces)   

DEV_WORKSPACE_NAME = os.getenv("DEV_WORKSPACE") 

def get_workspace_id(name, headers):
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    res = requests.get(url, headers=headers)
    
    for ws in res.json()["value"]:
        if ws["name"] == name:
            return ws["id"]
    
    return None

dev_workspace_id = get_workspace_id("Dev", headers)
print(dev_workspace_id)

url = f"https://api.powerbi.com/v1.0/myorg/groups/{dev_workspace_id}/reports"

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(url, headers=headers)
data = response.json()

# to get the report id,dataset_id for the report name requested by the user.
def report_details(report_name:str, data:dict):
    for report in data['value']:
        if report['name'] == report_name:
            return {
                "report_id": report["id"],
                "dataset_id": report["datasetId"],
                "report_name": report["name"]
            }

report_info = report_details("invoice-Dashboard", data)
print(report_info)

def generate_file_path(temp_dir, report_name):
    import re

    safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', report_name)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{safe_name}_{timestamp}.pbix"
    return os.path.join(temp_dir, file_name)

def export_pbix(workspace_id, report_id, report_name,headers):

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"

    res = requests.get(url, headers=headers, stream=True)

    TEMP_DIR = "temp"
    os.makedirs(TEMP_DIR, exist_ok=True)
    file_path = generate_file_path(TEMP_DIR, report_name)

    if res.status_code != 200:
        print("Export failed:", res.text)
        return None

    with open(file_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)

    print("Export completed:", file_path)
    return file_path

file_path_info=export_pbix(dev_workspace_id, report_info["report_id"], report_info["report_name"],headers)
print(file_path_info)

prod_workspace_id = get_workspace_id("Prod", headers)
print("Prod Workspace ID:", prod_workspace_id)


def upload_pbix(workspace_id, file_path,dataset_name, headers):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports?datasetDisplayName={dataset_name}&nameConflict=CreateOrOverwrite"

    with open(file_path, "rb") as f:
        files = {
            'file': (file_path, f, 'application/octet-stream')
        }

        res = requests.post(url, headers=headers, files=files)

    if res.status_code not in [200, 202]:
        print("Upload failed:", res.text)
        return None

    response = res.json()
    import_id = response["id"]

    print("Import ID:", import_id)
    return import_id

def check_import_status(workspace_id, import_id, headers, timeout=300, interval=5):

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports/{import_id}"

    start_time = time.time()
    attempts = 0
    max_attempts = 3



    while attempts < max_attempts:
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            raise Exception(f"Failed to check import status: {res.text}")

        data = res.json()
        status = data.get("importState")

        print(f"Attempt {attempts+1}: Import status - {status}")

        if status == "Succeeded":   # ✅ FIXED
            dataset_id = data["datasets"][0]["id"]
            report_id = data["reports"][0]["id"]
            return dataset_id, report_id

        elif status in ["Failed", "Cancelled"]:
            raise Exception(f"Import failed: {data}")

        time.sleep(interval)
        attempts += 1

    raise TimeoutError(f"Import did not complete within {timeout} seconds")

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"✅ Temporary file {file_path} deleted successfully")
    except Exception as e:
        print(f"❌ Failed to delete temporary file: {e}")


import_id=upload_pbix(prod_workspace_id, file_path_info, report_info["report_name"],headers)
dataset_id, new_report_id = check_import_status(prod_workspace_id, import_id, headers)
print("Dataset ID:", dataset_id)
print("Report ID:", new_report_id)
delete_file(file_path_info)

def delete_report(workspace_id, report_id, headers):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    
    res = requests.delete(url, headers=headers)
    
    if res.status_code == 200:
        print(f"✅ Report {report_id} deleted successfully")
    elif res.status_code == 404:
        print(f"⚠️ Report {report_id} not found")
    else:
        print(f"❌ Failed to delete report: {res.status_code}, {res.text}")

def delete_dataset(workspace_id, dataset_id, headers):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    
    res = requests.delete(url, headers=headers)
    
    if res.status_code == 200:
        print(f"✅ Dataset {dataset_id} deleted successfully")
    elif res.status_code == 404:
        print(f"⚠️ Dataset {dataset_id} not found")
    else:
        print(f"❌ Failed to delete dataset: {res.status_code}, {res.text}")

# delete_report(prod_workspace_id, new_report_id, headers)
# delete_dataset(prod_workspace_id, dataset_id, headers)

    



# def get_report_id(workspace_id, report_name, headers):
#     url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
#     res = requests.get(url, headers=headers)

#     for rpt in res.json()["value"]:
#         if rpt["name"] == report_name:
#             return rpt["id"], rpt["datasetId"]

#     return None,None



# report_id, dataset_id = get_report_id(dev_workspace_id, "Sales-Dashboard", headers)

# print("Report ID:", report_id)
# print("Dataset ID:", dataset_id)


# prod_workspace_id = get_workspace_id("Prod", headers)


# import time



# file_path = export_pbix(dev_workspace_id, report_id, headers, "exported.pbix")

# # Step 2: Upload
# import_id = upload_pbix(prod_workspace_id, file_path, headers)

# # Step 3: Wait + get dataset/report
# dataset_id, new_report_id = check_import_status(prod_workspace_id, import_id, headers)

# print("Dataset ID:", dataset_id)
# print("Report ID:", new_report_id)

# def delete_report(workspace_id, report_id, headers):
#     url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    
#     res = requests.delete(url, headers=headers)
    
#     if res.status_code == 200:
#         print(f"✅ Report {report_id} deleted successfully")
#     elif res.status_code == 404:
#         print(f"⚠️ Report {report_id} not found")
#     else:
#         print(f"❌ Failed to delete report: {res.status_code}, {res.text}")

# def delete_dataset(workspace_id, dataset_id, headers):
#     url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    
#     res = requests.delete(url, headers=headers)
    
#     if res.status_code == 200:
#         print(f"✅ Dataset {dataset_id} deleted successfully")
#     elif res.status_code == 404:
#         print(f"⚠️ Dataset {dataset_id} not found")
#     else:
#         print(f"❌ Failed to delete dataset: {res.status_code}, {res.text}")

# delete_report(prod_workspace_id, new_report_id, headers)
# delete_dataset(prod_workspace_id, dataset_id, headers)





# # url = "https://api.powerbi.com/v1.0/myorg/gateways"
# # res = requests.get(url, headers=headers)

# # print(res.json())



