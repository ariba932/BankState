from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List
import os
from extractors.pdf_extractor import extract_pdf_statement
from extractors.excel_extractor import extract_excel_statement
from integrations.docuclipper_api import extract_with_docuclipper
from mappers.camt053_mapper import map_to_camt053

router = APIRouter()

@router.post("/upload-statement")
async def upload_statement(
    files: List[UploadFile] = File(...),
    mode: str = Form("local"),
    api_key: str = Form(None)
):
    if len(files) > 100:
        return JSONResponse({"error": "Batch limit exceeded (max 100 files)"}, status_code=400)
    results = []
    for file in files:
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        if mode == "local":
            if file.filename.lower().endswith(".pdf"):
                extracted = extract_pdf_statement(temp_path)
            elif file.filename.lower().endswith((".xls", ".xlsx")):
                extracted = extract_excel_statement(temp_path)
            else:
                extracted = {"error": "Unsupported file type"}
        elif mode == "docuclipper":
            if not api_key:
                extracted = {"error": "API key required for DocuClipper mode"}
            else:
                extracted = extract_with_docuclipper(temp_path, api_key)
        else:
            extracted = {"error": "Unknown mode"}
        # Map to camt.053 (stub: expects 'transactions' key)
        camt053_xml = map_to_camt053(extracted.get("transactions", []))
        results.append({
            "filename": file.filename,
            "extracted": extracted,
            "camt053": camt053_xml
        })
        os.remove(temp_path)
    return JSONResponse({"results": results, "mode": mode})
