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
    """ 특정 pid가 포함된 CSV 파일을 삭제하는 함수 """
    if not os.path.exists(dir):
        logging.error(f"Error: Directory '{dir}' not found.")
        return False
    try: files = os.listdir(dir)
    except FileNotFoundError:
        logging.error(f"Error: Directory '{dir}' not found.")
        return False
    deleted_files = []
    for file in files:
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path) and file.endswith(".csv") and f"_{pid}_" in file:
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
            except Exception as e:
                logging.error(f"Error deleting {file_path}: {e}")
    if not deleted_files:
        logging.info(f"No matching files found for pid '{pid}' in directory '{dir}'.")
        return False
    logging.info(f"Deleted files: {deleted_files}")
    return True

@router.post("/ccp/clean_db")
async def api_clean_db_folder(payload: ccp_payload):
    """DB 폴더 정리 함수"""
    source = "/var/lib/mysql/csv"
    if not clean_db_folder(payload.pid, source):
        return JSONResponse(status_code=400, content={"message": "Directory not found or no matching files"})
    return JSONResponse(status_code=200, content={"message": "CSV files cleaned successfully."})

@router.post("/ccp/pull_db")
async def api_pull_db(payload: ccp_payload):
    """/var/lib/mysql/csv에서 /Data/API/Database_Files로 특정 pid 포함된 파일만 복사"""
    source = "/var/lib/mysql/csv"
    dest = f"/Data/API/ccp/{payload.pid}/DATABASE"
    try:
        os.makedirs(dest, exist_ok=True)
        files = os.listdir(source)
        copied_files = []
        for file in files:
            if os.path.isfile(os.path.join(source, file)) and file.endswith(".csv") and f"_{payload.pid}_" in file:
                shutil.copy2(os.path.join(source, file), os.path.join(dest, file))
                copied_files.append(file)
        if copied_files:
            return JSONResponse(status_code=200, content={"message": "Files copied successfully", "copied_files": copied_files})
        else:
            return JSONResponse(status_code=404, content={"message": "No matching files found for given pid"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Error copying files: {e}"})

@router.post("/ccp/push_db")
async def api_push_db(pid: int = Form(...), file: UploadFile = File(...)):
    """업로드된 CSV 파일을 /var/lib/mysql/csv 디렉터리에 저장하는 엔드포인트."""
    destination = "/var/lib/mysql/csv"
    try:
        os.makedirs(destination, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create destination directory '{destination}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create destination directory")
    file_path = os.path.join(destination, file.filename)
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logging.info(f"File '{file.filename}' saved to '{file_path}' for pid {pid}")
        return JSONResponse(status_code=200, content={"message": "File uploaded successfully", "filename": file.filename})
    except Exception as e:
        logging.error(f"Error saving file '{file.filename}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")