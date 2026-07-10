from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    status_code = 400
    error_code = "app_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
        self.message = message

class InvalidFileError(AppError):
    status_code = 400
    error_code = "invalid file"

class AnalyzerError(AppError):
    status_code = 500
    error_code = "analyzer error"

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "message": exc.message},
        )