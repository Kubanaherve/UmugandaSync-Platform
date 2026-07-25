"""
members.py
Owner: Sonia
Member management module for UmugandaSync.

Responsibilities
----------------
- Register, update, deactivate/activate, delete, and search members.
- Validate Rwandan National IDs, phone numbers, and email addresses.
- Prevent duplicate registrations (by phone / national ID).
- Provide CSV-ready export of member records for reporting.
- Expose `member_exists(member_id)` for use by other modules
  (Cynthia, Marvella, Rosette) exactly as before - signature preserved.

This module depends on:
- database.run_query(sql, params=None, fetch=None) -> cursor/id/rows
- helpers.*  (print_line, pause, get_non_empty, get_positive_int,
              confirm, today_string)
- languages.t(key) for translated menu strings

No changes are made to database.py, helpers.py, or languages.py.
"""

import csv
import io
import logging
import re

import database
import helpers
import languages


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
# A dedicated logger for this module so member-related events (creation,
# updates, deletions, validation failures) are traceable without polluting
# stdout, which is reserved for the interactive CLI output.
logger = logging.getLogger("umugandasync.members")
if not logger.handlers:
    _handler = logging.FileHandler("members.log", encoding="utf-8")
    _formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------
class MemberError(Exception):
    """Base exception for all member-related errors."""


class ValidationError(MemberError):
    """Raised when member input data fails validation rules."""


class DuplicateMemberError(MemberError):
    """Raised when a member with the same phone or national ID exists."""


class MemberNotFoundError(MemberError):
    """Raised when a requested member_id does not exist."""

