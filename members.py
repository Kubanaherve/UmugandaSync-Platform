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


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------
NATIONAL_ID_PATTERN = re.compile(r"^\d{16}$")
# Accepts formats like 0788123456 or +250788123456 or 250788123456
PHONE_PATTERN = re.compile(r"^(?:\+?250|0)7\d{8}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_national_id(national_id):
    """
    Validate a Rwandan National ID number.

    Rules:
        - Optional field (None or "" is allowed - caller decides).
        - If provided, must be exactly 16 digits.

    Returns the cleaned national_id (or None) on success.
    Raises ValidationError on failure.
    """
    if national_id is None or national_id == "":
        return None

    cleaned = national_id.strip()
    if not NATIONAL_ID_PATTERN.match(cleaned):
        raise ValidationError(
            "Invalid National ID: must be exactly 16 digits."
        )
    return cleaned


def validate_phone(phone):
    """
    Validate a Rwandan phone number.

    Accepts formats: 07XXXXXXXX, +2507XXXXXXXX, 2507XXXXXXXX.
    Returns the cleaned phone number on success.
    Raises ValidationError on failure.
    """
    if phone is None:
        raise ValidationError("Phone number is required.")

    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if not PHONE_PATTERN.match(cleaned):
        raise ValidationError(
            "Invalid phone number. Expected formats: 07XXXXXXXX or "
            "+2507XXXXXXXX."
        )
    return cleaned


def validate_email(email):
    """
    Validate an email address.

    Email is optional: None or "" returns None.
    Raises ValidationError if a non-empty value does not look like
    a valid email address.
    """
    if email is None or email.strip() == "":
        return None

    cleaned = email.strip()
    if not EMAIL_PATTERN.match(cleaned):
        raise ValidationError("Invalid email address format.")
    return cleaned


# --------------------------------------------------------------------------
# Reusable data-access helpers
# --------------------------------------------------------------------------
def get_member_by_id(member_id):
    """
    Fetch a single member row by ID.

    Returns the row (dict-like) or None if not found.
    """
    return database.run_query(
        "SELECT * FROM members WHERE member_id = %s",
        (member_id,),
        fetch="one",
    )


def require_member(member_id):
    """
    Fetch a member by ID, raising MemberNotFoundError if missing.

    Use this instead of get_member_by_id() when the caller cannot
    proceed without a valid member.
    """
    row = get_member_by_id(member_id)
    if row is None:
        raise MemberNotFoundError(f"No member found with ID {member_id}.")
    return row

