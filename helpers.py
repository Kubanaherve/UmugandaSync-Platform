import logging
import os
import re
from datetime import datetime, date, timedelta
from typing import Optional, Union

import config

logger = logging.getLogger(__name__)


class ExitRequested(Exception):
    """Raised when a user types 'exit' to abort the current operation."""


def input_with_exit(prompt_text: str) -> str:
    value = input(prompt_text).strip()
    if value.lower() == "exit":
        raise ExitRequested()
    return value

UMUGANDA_ACTIVITIES: list[str] = [
    "Road cleaning and pothole filling",
    "Drainage clearing before rain season",
    "Community garden planting",
    "Public water point cleaning",
    "School compound cleaning",
    "Tree planting around the village",
    "Market area sanitation",
    "Anti-erosion terracing support",
    "Health center surrounding cleanup",
    "General village sanitation (Umuganda)",
]

MONTH_NAMES: list[str] = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def clear_screen() -> None:
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    except Exception:
        print("\n" * 3)


def pause() -> None:
    import languages
    input(languages.t("press_enter"))


def confirm(question: str) -> bool:
    import languages
    answer = input_with_exit(question + languages.t("yn_prompt"))
    answer = answer.strip().lower()
    return answer in ("y", "yes", "o", "oui")


def get_non_empty(prompt_text: str) -> str:
    import languages
    while True:
        value = input_with_exit(prompt_text)
        if value:
            return value
        print(languages.t("empty_input"))


def get_positive_int(prompt_text: str) -> int:
    import languages
    while True:
        text = input_with_exit(prompt_text)
        if text.isdigit():
            return int(text)
        print(languages.t("invalid_number"))


def get_int_in_range(prompt_text: str, min_value: int, max_value: int) -> int:
    import languages
    while True:
        text = input_with_exit(prompt_text)
        ok = text.isdigit() or (text.startswith("-") and len(text) > 1 and text[1:].isdigit())
        if ok:
            number = int(text)
            if min_value <= number <= max_value:
                return number
        print(languages.t("invalid_range"), min_value, languages.t("and"), max_value)


def get_national_id(prompt_text: str) -> Optional[str]:
    """Prompt for a National ID. Empty input returns None (optional fields)."""
    while True:
        text = input_with_exit(prompt_text)
        if text == "":
            return None
        is_valid, msg = validate_national_id(text)
        if is_valid:
            return msg
        print(msg)


def get_required_national_id(prompt_text: str) -> str:
    """Prompt until a valid 16-digit Rwanda National ID is entered."""
    while True:
        text = input_with_exit(prompt_text)
        is_valid, msg = validate_national_id(text if text else None)
        if is_valid:
            return msg
        print(msg)


def get_date(prompt_text: str) -> str:
    import languages
    while True:
        text = input_with_exit(prompt_text + languages.t("date_prompt"))
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            print(languages.t("invalid_date"))


def today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_last_saturday(year: int, month: int) -> date:
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    days_since_saturday = (last_day.weekday() - 5) % 7
    return last_day - timedelta(days=days_since_saturday)


def ask_umuganda_month() -> Optional[tuple[str, int, int, str]]:
    import languages
    print()
    print("Umuganda happens on the LAST SATURDAY of each month.")
    print()

    current_year = datetime.now().year
    year_text = input_with_exit("Year (Enter for " + str(current_year) + "): ")
    if year_text == "":
        year = current_year
    else:
        if not year_text.isdigit():
            error("Invalid year.")
            return None
        year = int(year_text)
        if year < 2000 or year > 2100:
            error("Please enter a year between 2000 and 2100.")
            return None

    print()
    print("Choose month:")
    for i in range(1, 13):
        print(str(i) + ".", MONTH_NAMES[i])

    month = get_int_in_range("Month number (1-12): ", 1, 12)
    umuganda_day = get_last_saturday(year, month)
    date_text = umuganda_day.strftime("%Y-%m-%d")
    month_name = MONTH_NAMES[month]

    print()
    success(
        "Official Umuganda date: " + date_text
        + " (Last Saturday of " + month_name + " " + str(year) + ")"
    )
    return date_text, year, month, month_name


def choose_umuganda_remark(default_activity: Optional[str] = None) -> str:
    import languages
    print()
    print("Umuganda activity / remark:")
    for i, activity in enumerate(UMUGANDA_ACTIVITIES, 1):
        print(str(i) + ".", activity)
    print(str(len(UMUGANDA_ACTIVITIES) + 1) + ". Type my own remark")

    choice = get_int_in_range(
        "Choose activity (1-" + str(len(UMUGANDA_ACTIVITIES) + 1) + "): ",
        1,
        len(UMUGANDA_ACTIVITIES) + 1,
    )

    if choice == len(UMUGANDA_ACTIVITIES) + 1:
        return get_non_empty("Type Umuganda remark: ")

    return UMUGANDA_ACTIVITIES[choice - 1]


def print_line(title: str = "") -> None:
    print("-" * 50)
    if title:
        print(title)
        print("-" * 50)


def success(message: str) -> None:
    print()
    print("✓", message)
    print()


def error(message: str) -> None:
    print()
    print("✗", message)
    print()


def tip(message: str) -> None:
    print("  Tip:", message)


def info(message: str) -> None:
    print()
    print("ℹ", message)
    print()


def warning(message: str) -> None:
    print()
    print("⚠", message)
    print()


def format_date(date_val: Optional[Union[datetime, date, str]]) -> str:
    if date_val is None:
        return ""
    if isinstance(date_val, (datetime, date)):
        return date_val.strftime("%Y-%m-%d")
    return str(date_val)


def validate_phone(phone: Optional[str]) -> Optional[str]:
    if phone is None:
        return None
    phone = str(phone).strip()
    if len(phone) == config.PHONE_LENGTH and phone.startswith(config.ALLOWED_PHONE_PREFIXES[0]) and phone.isdigit():
        return phone
    if phone.startswith(config.ALLOWED_PHONE_PREFIXES[1]) and phone[1:].isdigit():
        return phone
    return None


def sanitize_string(text: Optional[str]) -> str:
    if text is None:
        return ""
    return str(text).strip()[:config.MAX_INPUT_LENGTH]


def get_optional_input(prompt_text: str, default: Optional[str] = None) -> Optional[str]:
    text = input_with_exit(prompt_text)
    return text if text else default


def validate_national_id(national_id: Optional[str]) -> tuple[bool, str]:
    import languages
    if national_id is None:
        return False, languages.t("nid_empty", fallback="National ID cannot be empty.")
    nid = str(national_id).strip()
    if len(nid) != config.NATIONAL_ID_LENGTH:
        return False, languages.t("nid_length_error", fallback="National ID must be exactly 16 digits.")
    if not nid.isdigit():
        return False, languages.t("nid_digit_error", fallback="National ID must contain only digits.")
    if not nid.startswith("1"):
        return False, languages.t("nid_prefix_error", fallback="Valid Rwanda National IDs start with '1'.")
    return True, nid


_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: Optional[str]) -> tuple[bool, str]:
    import languages
    if email is None or email.strip() == "":
        return False, languages.t("validate_email_empty", fallback="Email cannot be empty.")
    email = email.strip()
    if len(email) > config.MAX_INPUT_LENGTH:
        return False, "Email is too long."
    if _EMAIL_REGEX.match(email):
        return True, email
    return False, languages.t("validate_email_invalid", fallback="Invalid email format.")
