from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ApplicationError


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, debug=settings.debug)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request, exc: ApplicationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_app()
