from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os

from ccp import router as ccp_router

app = FastAPI(debug=True)

# 예외 핸들러
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    print(f"Unhandled error: {str(exc)}")  # 콘솔에 전체 예외 출력
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "error": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error: {exc.errors()}")  # 콘솔에 검증 오류 출력
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.get("/")
async def root():
    return {"message": "root of PMS Storage Server API."}

app.include_router(ccp_router, prefix="/api")