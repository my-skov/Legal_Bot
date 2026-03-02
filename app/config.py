from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    deepseek_timeout_seconds: float
    deepseek_max_retries: int
    deepseek_retry_base_delay_seconds: float
    legal_db_path: Path
    legal_db_config_path: Path
    retrieval_top_k: int
    max_question_length: int
    user_rate_limit_window_seconds: int
    user_rate_limit_max_requests: int
    user_min_interval_seconds: float
    google_sheet_enabled: bool
    google_spreadsheet_id: str
    google_worksheet_name: str
    google_service_account_file: Path
    sheets_max_retries: int
    sheets_retry_base_delay_seconds: float


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    load_dotenv()

    legal_db_path = Path(os.getenv("LEGAL_DB_PATH", "./legal_DB_768")).resolve()
    legal_db_config_path = Path(
        os.getenv("LEGAL_DB_CONFIG_PATH", str(legal_db_path / "config.json"))
    ).resolve()

    return Settings(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_timeout_seconds=float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "45")),
        deepseek_max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "4")),
        deepseek_retry_base_delay_seconds=float(
            os.getenv("DEEPSEEK_RETRY_BASE_DELAY_SECONDS", "1.0")
        ),
        legal_db_path=legal_db_path,
        legal_db_config_path=legal_db_config_path,
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
        max_question_length=int(os.getenv("MAX_QUESTION_LENGTH", "4000")),
        user_rate_limit_window_seconds=int(
            os.getenv("USER_RATE_LIMIT_WINDOW_SECONDS", "60")
        ),
        user_rate_limit_max_requests=int(
            os.getenv("USER_RATE_LIMIT_MAX_REQUESTS", "6")
        ),
        user_min_interval_seconds=float(os.getenv("USER_MIN_INTERVAL_SECONDS", "2.0")),
        google_sheet_enabled=_to_bool(os.getenv("GOOGLE_SHEET_ENABLED"), default=True),
        google_spreadsheet_id=os.getenv("GOOGLE_SPREADSHEET_ID", ""),
        google_worksheet_name=os.getenv("GOOGLE_WORKSHEET_NAME", "Sheet1"),
        google_service_account_file=Path(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "./google-service-account.json")
        ).resolve(),
        sheets_max_retries=int(os.getenv("SHEETS_MAX_RETRIES", "4")),
        sheets_retry_base_delay_seconds=float(
            os.getenv("SHEETS_RETRY_BASE_DELAY_SECONDS", "1.0")
        ),
    )

