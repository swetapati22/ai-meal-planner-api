"""
Main FastAPI application (AI Meal Planner API) entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import routes
from app.core.config import settings
import logging

#Configure logging:
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

#Lifespan event handler:
@asynccontextmanager
async def lifespan(app: FastAPI):
    #Startup:
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    yield
    #Shutdown:
    logger.info(f"Shutting down {settings.app_name}")

#Create FastAPI app:
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Personalized Meal Planner API",
    lifespan=lifespan
)

#Add CORS middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Include routers - registering the API endpoints:
app.include_router(routes.router)

#Exception handler for 422 validation errors:
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

