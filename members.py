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


def is_duplicate_phone(phone, exclude_member_id=None):
    """
    Check whether `phone` is already registered to another member.

    exclude_member_id lets update flows ignore the member's own record.
    """
    if exclude_member_id is None:
        row = database.run_query(
            "SELECT member_id FROM members WHERE phone = %s",
            (phone,),
            fetch="one",
        )
    else:
        row = database.run_query(
            "SELECT member_id FROM members WHERE phone = %s AND member_id <> %s",
            (phone, exclude_member_id),
            fetch="one",
        )
    return row is not None


def is_duplicate_national_id(national_id, exclude_member_id=None):
    """
    Check whether `national_id` is already registered to another member.
    Skipped automatically when national_id is None (optional field).
    """
    if national_id is None:
        return False

    if exclude_member_id is None:
        row = database.run_query(
            "SELECT member_id FROM members WHERE national_id = %s",
            (national_id,),
            fetch="one",
        )
    else:
        row = database.run_query(
            "SELECT member_id FROM members WHERE national_id = %s AND member_id <> %s",
            (national_id, exclude_member_id),
            fetch="one",
        )
    return row is not None


def member_exists(member_id):
    """
    Return True/False for whether a member_id exists.

    Preserved for other modules (Cynthia, Marvella, Rosette) that
    already depend on this exact function name and signature.
    """
    return get_member_by_id(member_id) is not None


# --------------------------------------------------------------------------
# CSV export
# --------------------------------------------------------------------------
def members_to_csv(rows):
    """
    Convert a list of member row dicts into a CSV-formatted string.

    Useful for reporting/export features elsewhere in the project.
    Returns an empty string if `rows` is empty or None.
    """
    if not rows:
        return ""

    buffer = io.StringIO()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))
    return buffer.getvalue()


def export_members_csv(filepath="members_export.csv"):
    """
    Query all members and write them to a CSV file on disk.

    Returns the number of members exported.
    """
    rows = database.run_query(
        "SELECT * FROM members ORDER BY member_id", fetch="all"
    )
    csv_text = members_to_csv(rows)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)

    count = len(rows) if rows else 0
    logger.info("Exported %d members to CSV file '%s'.", count, filepath)
    return count


# --------------------------------------------------------------------------
# Menu
# --------------------------------------------------------------------------
def member_menu():
    """Interactive CLI menu for member management."""
    running = True
    while running:
        helpers.print_line(languages.t("member_menu"))
        print(languages.t("m1"))
        print(languages.t("m2"))
        print(languages.t("m3"))
        print(languages.t("m4"))
        print(languages.t("m5"))
        print(languages.t("m6"))
        print(languages.t("m7"))
        print(languages.t("m0"))
        choice = input(languages.t("enter_choice")).strip()

        if choice == "1":
            add_member()
        elif choice == "2":
            view_members()
        elif choice == "3":
            search_member()
        elif choice == "4":
            update_member()
        elif choice == "5":
            delete_member()
        elif choice == "6":
            set_member_status("Inactive")
        elif choice == "7":
            set_member_status("Active")
        elif choice == "0":
            running = False
        else:
            print(languages.t("invalid_choice"))


# --------------------------------------------------------------------------
# Create
# --------------------------------------------------------------------------
def add_member():
    """
    Interactive flow to register a new member.

    Validates National ID (optional), phone (required), and email
    (optional) before insert. Prevents duplicate phone/National ID.
    """
    helpers.print_line("ADD MEMBER")

    try:
        national_id_raw = input("National ID (optional, Enter to skip): ").strip()
        national_id = validate_national_id(national_id_raw)

        first_name = helpers.get_non_empty("First name: ")
        last_name = helpers.get_non_empty("Last name: ")

        phone_raw = helpers.get_non_empty("Phone number: ")
        phone = validate_phone(phone_raw)

        email_raw = input("Email (optional, Enter to skip): ").strip()
        email = validate_email(email_raw)

        if is_duplicate_phone(phone):
            raise DuplicateMemberError(
                "This phone number is already registered."
            )
        if is_duplicate_national_id(national_id):
            raise DuplicateMemberError(
                "This National ID is already registered."
            )

        village = helpers.get_non_empty("Village: ")
        cell_name = helpers.get_non_empty("Cell: ")

        print("Gender: 1=Male  2=Female  3=Other")
        g = input("Choose gender: ").strip()
        if g == "1":
            gender = "Male"
        elif g == "2":
            gender = "Female"
        else:
            gender = "Other"

        date_registered = helpers.today_string()

        new_id = _insert_member(
            national_id, first_name, last_name, phone, email,
            village, cell_name, gender, date_registered,
        )

        print("Member added successfully. Member ID:", new_id)
        logger.info(
            "Added member #%s (%s %s, phone=%s).",
            new_id, first_name, last_name, phone,
        )

    except (ValidationError, DuplicateMemberError) as exc:
        print("Error:", exc)
        logger.warning("add_member failed: %s", exc)

    helpers.pause()


def _insert_member(national_id, first_name, last_name, phone, email,
                    village, cell_name, gender, date_registered):
    """
    Low-level insert. Kept separate from add_member() so it is
    reusable (e.g. for bulk import features) without re-prompting
    the user for input.
    """
    sql = """
        INSERT INTO members
        (national_id, first_name, last_name, phone, email, village,
         cell_name, gender, date_registered, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
    """
    values = (
        national_id, first_name, last_name, phone, email,
        village, cell_name, gender, date_registered,
    )
    new_id = database.run_query(sql, values)
    if new_id is None:
        raise MemberError("Database insert failed for new member.")
    return new_id

