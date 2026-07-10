from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "AI PHOTO DETECTOR"
    environment: str = "local"  # local, staging, production
    debug: bool = False
    database_url: str = "sqlite:///./app.db"
    api_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")


    max_upload_size: int = 10
    allowed_extensions: list[str] = Field(default_factory=lambda: ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg", "heic", "heif","pdf"])
    allowed_mime_types: list[str] = Field(default_factory=lambda: ["image/jpeg", "image/png"])
   
   
    tesseract_cmd: str | None = None
    
    ocr_timeout: int = 30

    historical_rules_path: str = "historical_rules.json"

    signal_weights: dict[str, float] = Field(default_factory=lambda: {
        "Metadata Analysis": 0.3,
        "OCR": 0.4,
        "Density Analysis": 0.3,
        "Texture Analysis": 0.3,
        "Forensic Analysis": 0.4,
        "Advanced Forensic Analysis": 0.5,
        "Content Profile": 0.4,
        "Synthetic ID Verification": 0.5,
        "Historical Validation": 0.4
    })



@lru_cache()
def get_settings() -> Settings:
    return Settings()

