from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.services.errors import ServiceError

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root() -> dict:
    return {"message": f"{settings.APP_NAME} API is running"}
