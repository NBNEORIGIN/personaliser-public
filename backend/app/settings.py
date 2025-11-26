from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    JOBS_DIR: Path = DATA_DIR / "jobs"
    PREVIEWS_DIR: Path = DATA_DIR / "previews"
    UPLOADS_DIR: Path = DATA_DIR / "storage" / "uploads"
    PHOTOS_DIR: Path = DATA_DIR / "photos"
    DEFAULT_SEED: int = 42
    DOWNLOAD_CONCURRENCY: int = 4
    DOWNLOAD_TIMEOUT_S: int = 30
    MAX_ZIP_MB: int = 25
    USER_AGENT: str = "NBNE-Ingest/1.0"
    DOWNLOAD_TMP_DIR: Path = Path("/tmp/downloads")
    ALLOW_EXTERNAL_DOWNLOADS: bool = True
    CLEAN_PHOTOS_ON_START: bool = True
    # SKU map reload (seconds). 0 disables background reload.
    SKU_MAP_RELOAD_SEC: int = 0
    # Storage
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    PRESIGN_EXPIRES_S: int = 3600
    # SKU list CSV (container path; mount host ./assets to /app/assets)
    # On Render, use relative path from backend directory
    SKULIST_PATH: Path = BASE_DIR.parent / "assets" / "SKULIST.csv"
    # Graphics directory (images embedded into SVG)
    GRAPHICS_DIR: Path = BASE_DIR.parent / "assets" / "graphics"
    # Auth0 / OIDC
    AUTH0_DOMAIN: str | None = None
    AUTH0_AUDIENCE: str | None = None
    AUTH0_ISSUER: str | None = None
    AUTH0_ALGORITHMS: list[str] = ["RS256"]
    AUTH0_JWKS_CACHE_MIN: int = 600
    BYPASS_AUTH_FOR_TESTS: bool = True
    # Monitoring
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str = "development"
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100

    class Config:
        env_prefix = "APP_"
        env_file = str((Path(__file__).parent.parent / ".env"))
        extra = "ignore"  # Ignore extra fields from .env file

settings = Settings()

# ensure directories exist (with error handling for read-only filesystems)
try:
    settings.JOBS_DIR.mkdir(parents=True, exist_ok=True)
    settings.PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    pass  # May be read-only in production

try:
    settings.DOWNLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)
    settings.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    pass  # /tmp should be writable
