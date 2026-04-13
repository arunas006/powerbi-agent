from __future__ import annotations
import requests
from src.config import get_settings

settings = get_settings()

def get_access_token(tenant_id, client_id, client_secret) -> str:

    """
    This function retrieves an access token from Azure AD using the client credentials flow.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload  = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        token : str = response.json().get("access_token")
        if not token:
            raise ValueError("Access token not found in the response.")
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to retrieve access token: {e}")
    
def get_auth_headers() -> dict:
    """
    This function constructs the authorization headers for API requests.
    """
    token = get_access_token(
        tenant_id=settings.TENANT_ID.get_secret_value(),
        client_id=settings.CLIENT_ID.get_secret_value(),
        client_secret=settings.CLIENT_SECRET.get_secret_value()
    )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
       
def health_check() -> str:
    try:
        settings = get_settings()
        url = f"{settings.POWER_BI_BASE_URL}/groups"
        headers = get_auth_headers()

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return "Healthy"
        else:
            return f"Unhealthy (status: {response.status_code})"
    except Exception as e:
        return f"Unhealthy (error: {str(e)})"


if __name__ == "__main__":
    access_token = get_auth_headers()
    print(access_token)