from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
import os

from database import engine
import models
from routes import auth, mentor

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MyCoach API", version="1.0.0")

# Allow all localhost ports (Vite may use 5173, 5174, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Ensure CORS headers are present even on error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
    )

# Serve uploaded CVs (optional, for admin use)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(mentor.router)


@app.get("/")
def root():
    return {"status": "MyCoach API running"}
