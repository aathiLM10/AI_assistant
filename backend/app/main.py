from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "AI Assistant backend service started",
        extra={"extra_fields": {"environment": settings.ENVIRONMENT, "model": settings.GEMINI_MODEL}}
    )
    yield
    logger.info("AI Assistant backend service shutting down")


app = FastAPI(
    title="AI Assistant API",
    description=(
        "Learning-focused Generative AI backend architecture demonstrating clean separation: "
        "Route -> ChatService -> PromptService -> LLMService -> Provider -> Gemini."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Chat",
            "description": "Operations for querying the Gemini-powered generative AI assistant."
        },
        {
            "name": "System",
            "description": "System health and status inspection."
        }
    ]
)

# Configure Cross-Origin Resource Sharing (CORS) for Next.js frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(chat.router)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns service availability and configured model."
)
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "model": settings.GEMINI_MODEL
    }
