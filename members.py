"""
members.py
Member management module for UmugandaSync.

Responsibilities
----------------
- Register, update, deactivate/activate, delete, and search members.
- Primary key is the 16-digit Rwanda National ID (national_id).
- Validate National IDs, phone numbers, and email addresses.
- Prevent duplicate registrations (by phone / national ID).
- Provide CSV-ready export of member records for reporting.
- Expose `member_exists(national_id)` for use by other modules
  (attendance, projects, tools) — argument is the National ID string.

This module depends on:
- database.run_query(sql, params=None, fetch=None) -> cursor/id/rows
- helpers.*  (print_line, pause, get_non_empty, get_required_national_id,
              confirm, today_string)
- languages.t(key) for translated menu strings
"""

import csv
import io
import logging
import re

import database
import helpers
import languages


logger = logging.getLogger("umugandasync.members")
if not logger.handlers:
    _handler = logging.FileHandler("members.log", encoding="utf-8")
    _formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


class MemberError(Exception):
    """Base exception for all member-related errors."""


class ValidationError(MemberError):
    """Raised when member input data fails validation rules."""


class DuplicateMemberError(MemberError):
    """Raised when a member with the same phone or national ID exists."""


class MemberNotFoundError(MemberError):
    """Raised when a requested national_id does not exist."""


NATIONAL_ID_PATTERN = re.compile(r"^\d{16}$")
PHONE_PATTERN = re.compile(r"^(?:\+?250|0)7\d{8}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_national_id(national_id):
    """
    Validate a Rwandan National ID number (required primary key).

    Must be exactly 16 digits. Returns the cleaned national_id on success.
    Raises ValidationError on failure.
    """
    if national_id is None or str(national_id).strip() == "":
        raise ValidationError(
            "National ID is required and must be exactly 16 digits."
        )

    cleaned = str(national_id).strip()
    if not NATIONAL_ID_PATTERN.match(cleaned):
        raise ValidationError(
            "Invalid National ID: must be exactly 16 digits."
        )
    return cleaned


def validate_phone(phone):
    """Validate a Rwandan phone number. Raises ValidationError on failure."""
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
    """Email is optional: None or "" returns None."""
    if email is None or email.strip() == "":
        return None

    cleaned = email.strip()
    if not EMAIL_PATTERN.match(cleaned):
        raise ValidationError("Invalid email address format.")
    return cleaned


def get_member_by_id(national_id):
    """Fetch a single member row by National ID (primary key)."""
    return database.run_query(
        "SELECT * FROM members WHERE national_id = %s",
        (national_id,),
        fetch="one",
    )


def require_member(national_id):
    """Fetch a member by National ID, or raise MemberNotFoundError."""
    row = get_member_by_id(national_id)
    if row is None:
        raise MemberNotFoundError(
            f"No member found with National ID {national_id}."
        )
    return row


def is_duplicate_phone(phone, exclude_national_id=None):
    """Check whether phone is already registered to another member."""
    if exclude_national_id is None:
        row = database.run_query(
            "SELECT national_id FROM members WHERE phone = %s",
            (phone,),
            fetch="one",
        )
    else:
        row = database.run_query(
            """
            SELECT national_id FROM members
            WHERE phone = %s AND national_id <> %s
            """,
            (phone, exclude_national_id),
            fetch="one",
        )
    return row is not None


def is_duplicate_national_id(national_id, exclude_national_id=None):
    """Check whether national_id is already registered."""
    if national_id is None:
        return False

    if exclude_national_id is None:
        row = database.run_query(
            "SELECT national_id FROM members WHERE national_id = %s",
            (national_id,),
            fetch="one",
        )
    else:
        row = database.run_query(
            """
            SELECT national_id FROM members
            WHERE national_id = %s AND national_id <> %s
            """,
            (national_id, exclude_national_id),
            fetch="one",
        )
    return row is not None


def member_exists(national_id):
    """
    Return True/False for whether a National ID exists.

    Other modules pass the 16-digit National ID — the same value stored
    as member_id in attendance / tool_borrows / projects.leader_member_id.
    """
    return get_member_by_id(national_id) is not None


def members_to_csv(rows):
    """Convert member rows to a CSV string."""
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
    """Query all members and write them to a CSV file on disk."""
    rows = database.run_query(
        "SELECT * FROM members ORDER BY national_id", fetch="all"
    )
    csv_text = members_to_csv(rows)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)

    count = len(rows) if rows else 0
    logger.info("Exported %d members to CSV file '%s'.", count, filepath)
    return count


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


def add_member():
    """Register a new member. National ID (16 digits) is the primary key."""
    helpers.print_line("ADD MEMBER")

    try:
        national_id = helpers.get_required_national_id(
            "National ID (16 digits): "
        )
        national_id = validate_national_id(national_id)

        first_name = helpers.get_non_empty("First name: ")
        last_name = helpers.get_non_empty("Last name: ")

        phone_raw = helpers.get_non_empty("Phone number: ")
        phone = validate_phone(phone_raw)

        email_raw = input("Email (optional, Enter to skip): ").strip()
        email = validate_email(email_raw)

        if is_duplicate_national_id(national_id):
            raise DuplicateMemberError(
                "This National ID is already registered."
            )
        if is_duplicate_phone(phone):
            raise DuplicateMemberError(
                "This phone number is already registered."
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

        print("Member added successfully. National ID:", new_id)
        logger.info(
            "Added member %s (%s %s, phone=%s).",
            new_id, first_name, last_name, phone,
        )

    except MemberError as exc:
        print("Error:", exc)
        logger.warning("add_member failed: %s", exc)

    helpers.pause()


def _insert_member(national_id, first_name, last_name, phone, email,
                    village, cell_name, gender, date_registered):
    """Low-level insert. Returns the national_id primary key on success."""
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
    result = database.run_query(sql, values)
    if result is None:
        raise MemberError("Database insert failed for new member.")
    return national_id


def view_members():
    """Display all members in a simple tabular text listing."""
    helpers.print_line("ALL MEMBERS")
    rows = database.run_query(
        "SELECT * FROM members ORDER BY last_name, first_name", fetch="all"
    )

    if not rows:
        print("No members found.")
    else:
        for row in rows:
            print(
                row["national_id"], "|",
                row["first_name"], row["last_name"], "|",
                row["phone"], "|", row["village"], "/", row["cell_name"], "|",
                row["gender"], "|", row["status"],
            )
        print("Total members:", len(rows))
    helpers.pause()


def search_member():
    """Interactive search by National ID, Name, or Phone."""
    helpers.print_line("SEARCH MEMBER")
    print("1. By National ID")
    print("2. By Name")
    print("3. By Phone")
    choice = input("Enter choice: ").strip()

    try:
        rows = _run_search(choice)
    except ValidationError as exc:
        print("Error:", exc)
        helpers.pause()
        return

    if rows is None:
        print("Invalid choice.")
    elif len(rows) == 0:
        print("No member found.")
    else:
        for row in rows:
            print(
                "NID:", row["national_id"],
                "| Name:", row["first_name"], row["last_name"],
                "| Phone:", row["phone"],
                "| Village:", row["village"],
                "| Status:", row["status"],
            )
    helpers.pause()


def _run_search(choice):
    """Execute the DB query for search_member() based on menu choice."""
    if choice == "1":
        national_id = helpers.get_required_national_id("National ID: ")
        return database.run_query(
            "SELECT * FROM members WHERE national_id = %s",
            (national_id,),
            fetch="all",
        )
    elif choice == "2":
        name = helpers.get_non_empty("Name (first or last): ")
        like_name = "%" + name + "%"
        return database.run_query(
            """
            SELECT * FROM members
            WHERE first_name LIKE %s OR last_name LIKE %s
            ORDER BY first_name
            """,
            (like_name, like_name),
            fetch="all",
        )
    elif choice == "3":
        phone_raw = helpers.get_non_empty("Phone: ")
        phone = validate_phone(phone_raw)
        return database.run_query(
            "SELECT * FROM members WHERE phone = %s",
            (phone,),
            fetch="all",
        )
    return None


def update_member():
    """Interactive flow to update an existing member's editable fields."""
    helpers.print_line("UPDATE MEMBER")

    try:
        national_id = helpers.get_required_national_id(
            "National ID to update: "
        )
        row = require_member(national_id)

        print("Current:", row["first_name"], row["last_name"], row["phone"])
        first_name = helpers.get_non_empty("New first name: ")
        last_name = helpers.get_non_empty("New last name: ")

        phone_raw = helpers.get_non_empty("New phone: ")
        phone = validate_phone(phone_raw)

        email_raw = input("New email (optional, Enter to skip): ").strip()
        email = validate_email(email_raw)

        village = helpers.get_non_empty("New village: ")
        cell_name = helpers.get_non_empty("New cell: ")

        if is_duplicate_phone(phone, exclude_national_id=national_id):
            raise DuplicateMemberError(
                "Phone already used by another member."
            )

        _update_member_row(
            national_id, first_name, last_name, phone, email,
            village, cell_name,
        )
        print("Member updated successfully.")
        logger.info("Updated member %s.", national_id)

    except MemberError as exc:
        print("Error:", exc)
        logger.warning("update_member failed: %s", exc)

    helpers.pause()


def _update_member_row(national_id, first_name, last_name, phone, email,
                        village, cell_name):
    """Low-level UPDATE statement, isolated for reuse/testing."""
    result = database.run_query(
        """
        UPDATE members
        SET first_name=%s, last_name=%s, phone=%s, email=%s,
            village=%s, cell_name=%s
        WHERE national_id=%s
        """,
        (first_name, last_name, phone, email, village, cell_name, national_id),
    )
    if result is None:
        raise MemberError(
            f"Database update failed for member {national_id}."
        )
    return result


def delete_member():
    """Interactive flow to permanently delete a member."""
    helpers.print_line("DELETE MEMBER")

    try:
        national_id = helpers.get_required_national_id(
            "National ID to delete: "
        )
        row = require_member(national_id)

        print("You will delete:", row["first_name"], row["last_name"])
        ok = helpers.confirm("Are you sure? This cannot be undone")
        if not ok:
            print("Delete cancelled.")
            helpers.pause()
            return

        result = database.run_query(
            "DELETE FROM members WHERE national_id = %s",
            (national_id,),
        )
        if result is not None:
            print("Member deleted.")
            logger.info("Deleted member %s.", national_id)
        else:
            print("Could not delete. Maybe they have attendance or borrows.")
            print("Tip: deactivate the member instead.")
            logger.warning(
                "Delete blocked for member %s (likely FK constraint).",
                national_id,
            )

    except MemberError as exc:
        print("Error:", exc)
        logger.warning("delete_member failed: %s", exc)

    helpers.pause()


def set_member_status(new_status):
    """Set a member's status to 'Active' or 'Inactive'."""
    helpers.print_line("SET MEMBER STATUS: " + new_status)

    try:
        national_id = helpers.get_required_national_id("National ID: ")
        require_member(national_id)

        result = database.run_query(
            "UPDATE members SET status = %s WHERE national_id = %s",
            (new_status, national_id),
        )
        if result is not None:
            print("Member status changed to", new_status)
            logger.info(
                "Member %s status set to %s.", national_id, new_status
            )
        else:
            print("Failed to update status.")
            logger.warning(
                "Status update failed for member %s.", national_id
            )

    except MemberError as exc:
        print("Error:", exc)
        logger.warning("set_member_status failed: %s", exc)

    helpers.pause()
