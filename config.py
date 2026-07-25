"""
Application configuration constants for UmugandaSync.

All settings are defined here as module-level constants.
Environment variables (with UMUGANDA_ prefix) override defaults.
"""

import os
from typing import Final

APP_NAME: Final[str] = "UmugandaSync"
APP_VERSION: Final[str] = "2.1.0"

DB_HOST: str = os.getenv("UMUGANDA_DB_HOST", "localhost")
DB_USER: str = os.getenv("UMUGANDA_DB_USER", "root")
DB_PASSWORD: str = os.getenv("UMUGANDA_DB_PASSWORD", "")
DB_NAME: str = os.getenv("UMUGANDA_DB_NAME", "umuganda_sync")

NATIONAL_ID_LENGTH: Final[int] = 16
NATIONAL_ID_PREFIX: Final[str] = "1"

CSV_EXPORT_DIR: str = os.getenv("UMUGANDA_CSV_DIR", "exports")
CSV_DELIMITER: Final[str] = ","
CSV_ENCODING: Final[str] = "utf-8-sig"
CSV_MAX_ROWS: Final[int] = 50000

MAX_LOGIN_ATTEMPTS: Final[int] = 3
MAX_INPUT_LENGTH: Final[int] = 200
MAX_SEARCH_RESULTS: Final[int] = 100
ALLOWED_PHONE_PREFIXES: Final[tuple[str, ...]] = ("07", "+2507")
PHONE_LENGTH: Final[int] = 10

DEFAULT_PAGE_SIZE: Final[int] = 50

SESSION_TIMEOUT_MINUTES: Final[int] = 30
SESSION_MAX_IDLE_MINUTES: Final[int] = 15

LOG_LEVEL: str = os.getenv("UMUGANDA_LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
LOG_DIR: str = os.getenv("UMUGANDA_LOG_DIR", "logs")
