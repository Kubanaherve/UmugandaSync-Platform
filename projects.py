"""
projects.py
Owner: Sonia — Project Management module for UmugandaSync.

Clean architecture (single module, layered sections):
    1. Exceptions & constants
    2. Validation
    3. Data access (repository)
    4. Domain services (progress, deadlines, overdue)
    5. Presentation (display, alerts, reports)
    6. Interactive UI handlers + menu
    7. Public APIs consumed by notifications / dashboard

Features:
    - Add project
    - Edit project
    - Complete project
    - Progress tracking
    - Deadline monitoring
    - Overdue alerts
    - Project reports

Other modules should call:
    project_menu(), list_overdue_project_names(), count_overdue_projects()
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional

import database
import helpers
import languages

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_STATUSES: tuple[str, ...] = ("Pending", "Ongoing", "Completed", "Cancelled")
ACTIVE_STATUSES: tuple[str, ...] = ("Pending", "Ongoing")
MIN_NAME_LENGTH: int = 2
MAX_NAME_LENGTH: int = 100
MAX_LOCATION_LENGTH: int = 100
MAX_DESCRIPTION_LENGTH: int = 2000
DEADLINE_WARN_DAYS: int = 7  # nearing deadline window


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class ProjectError(Exception):
    """Base error for project management failures."""


class ProjectValidationError(ProjectError):
    """Raised when project input fails validation."""


class ProjectNotFoundError(ProjectError):
    """Raised when a project ID does not exist."""


class ProjectDataError(ProjectError):
    """Raised when a database operation fails unexpectedly."""
