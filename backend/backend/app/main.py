from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings
from app.schemas.common import ApiErrorDetail, ApiErrorResponse

settings = get_settings()

app = FastAPI(
    title="ConsentShield API",
    version=settings.api_version,
    description=(
        "Privacy-first cookie/consent analysis backend. Read-only by "
        "default; automatic protection requires an explicit user "
        "preference. See docs/api-contract.md for the authoritative "
        "request/response contract."
    ),
)

# Allows the ConsentShield frontend (served from a different origin/port,
# e.g. the Vite dev server) to call this API directly from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic validation failures (including the contradictory-preference
    # checks in schemas/preferences.py) surface here as structured 422s.
    # exc.errors() can include a raw exception object in "ctx" (e.g. for
    # errors raised inside a model_validator), which isn't JSON
    # serializable -- strip down to plain, safe fields only.
    safe_errors = [
        {"type": e.get("type"), "loc": list(e.get("loc", [])), "msg": e.get("msg")}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiErrorResponse(
            error=ApiErrorDetail(
                code="validation_error",
                message="The request could not be validated.",
                details={"errors": safe_errors},
            )
        ).model_dump(mode="json"),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = {
        401: "unauthorized",
        404: "not_found",
        409: "conflict",
        422: "unprocessable_entity",
    }.get(exc.status_code, "error")
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(
            error=ApiErrorDetail(code=code, message=str(exc.detail))
        ).model_dump(mode="json"),
    )
