import requests
from typing import Dict, Any

# Integrates with DocuClipper API for OCR/extraction

def extract_with_docuclipper(file_path: str, api_key: str) -> Dict[str, Any]:
    url = "https://api.docuclipper.com/v1/bank-statements/extract"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": open(file_path, "rb")}
    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    finally:
        files["file"].close()
