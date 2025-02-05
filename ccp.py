from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import os, shutil, tarfile, logging

router = APIRouter()

class ccp_payload(BaseModel):
    pid: int

def clean_db_folder(pid, dir):
    try: files = os.listdir(dir)
    except FileNotFoundError: print(f"Error: Directory '{dir}' not found."); return False
    deleted_files = []
    for file in files:
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path) and file.endswith(".csv") and f"_{pid}_" in file:
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
            except Exception as e: print(f"Error deleting {file_path}: {e}")

@router.post("/ccp/pull_db")
async def api_pull_db(payload: ccp_payload):
    """/Data/MySQL/csv에서 /Data/API/Database_Files로 특정 pid 포함된 파일만 복사"""
    source = "/Data/MySQL/csv"
    dest = "/Data/API/Database_Files"
    try:
        os.makedirs(dest, exist_ok=True)
        files = os.listdir(source)
        copied_files = []
        for file in files:
            if os.path.isfile(os.path.join(source, file)) and file.endswith(".csv") and f"_{payload.pid}_" in file:
                shutil.copy2(os.path.join(source, file), os.path.join(dest, file))
                copied_files.append(file)
        if copied_files:
            if not clean_db_folder(payload.pid, source):
                return JSONResponse(status_code=400, content={"message": "Directory not found or no matching files"})
            return JSONResponse(status_code=200, content={"message": "Files copied successfully", "copied_files": copied_files})
        else:
            return JSONResponse(status_code=404, content={"message": "No matching files found for given pid"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error copying files: {e}"})