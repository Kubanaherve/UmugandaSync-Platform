# helpers.py
# shared beginner helpers for UmugandaSync

import os
from datetime import datetime, date, timedelta
import languages

# Real Umuganda activities used as remarks
UMUGANDA_ACTIVITIES = [
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

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def clear_screen():
    # works on Mac/Linux; on Windows uses cls
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    except Exception:
        print("\n" * 3)


def pause():
    input(languages.t("press_enter"))


def confirm(question):
    answer = input(question + languages.t("yn_prompt"))
    answer = answer.strip().lower()
    if answer == "y" or answer == "yes" or answer == "o" or answer == "oui":
        return True
    return False


def get_non_empty(prompt_text):
    while True:
        value = input(prompt_text)
        value = value.strip()
        if value != "":
            return value
        print(languages.t("empty_input"))


def get_positive_int(prompt_text):
    while True:
        text = input(prompt_text)
        text = text.strip()
        if text.isdigit():
            return int(text)
        print(languages.t("invalid_number"))


def get_int_in_range(prompt_text, min_value, max_value):
    while True:
        text = input(prompt_text)
        text = text.strip()
        ok = False
        if text.isdigit():
            ok = True
        if text.startswith("-") and len(text) > 1:
            if text[1:].isdigit():
                ok = True
        if ok:
            number = int(text)
            if number >= min_value and number <= max_value:
                return number
        print(languages.t("invalid_range"), min_value, languages.t("and"), max_value)


def get_date(prompt_text):
    while True:
        text = input(prompt_text + languages.t("date_prompt"))
        text = text.strip()
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            print(languages.t("invalid_date"))


def today_string():
    return datetime.now().strftime("%Y-%m-%d")


def get_last_saturday(year, month):
    """
    Umuganda is always on the LAST Saturday of the month.
    Works for any year / any month.
    """
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)

    last_day = next_month_first - timedelta(days=1)
    # Monday=0 ... Saturday=5
    days_since_saturday = (last_day.weekday() - 5) % 7
    last_saturday = last_day - timedelta(days=days_since_saturday)
    return last_saturday


def ask_umuganda_month():
    """
    Leader only chooses YEAR + MONTH.
    System calculates the official Umuganda date (last Saturday).
    Returns: date_text (YYYY-MM-DD), year, month, month_name
    """
    print()
    print("Umuganda happens on the LAST SATURDAY of each month.")
    print()

    current_year = datetime.now().year
    year_text = input("Year (Enter for " + str(current_year) + "): ").strip()
    if year_text == "":
        year = current_year
    else:
        if year_text.isdigit() == False:
            error("Invalid year.")
            return None
        year = int(year_text)
        if year < 2000 or year > 2100:
            error("Please enter a year between 2000 and 2100.")
            return None

    print()
    print("Choose month:")
    i = 1
    while i <= 12:
        print(str(i) + ".", MONTH_NAMES[i])
        i = i + 1

    month = get_int_in_range("Month number (1-12): ", 1, 12)
    umuganda_day = get_last_saturday(year, month)
    date_text = umuganda_day.strftime("%Y-%m-%d")
    month_name = MONTH_NAMES[month]

    print()
    success(
        "Official Umuganda date: " + date_text +
        " (Last Saturday of " + month_name + " " + str(year) + ")"
    )
    return date_text, year, month, month_name


def choose_umuganda_remark(default_activity=None):
    """
    Choose a real Umuganda activity remark.
    Always saves a remark (never empty for Umuganda sessions).
    """
    print()
    print("Umuganda activity / remark:")
    i = 0
    while i < len(UMUGANDA_ACTIVITIES):
        print(str(i + 1) + ".", UMUGANDA_ACTIVITIES[i])
        i = i + 1
    print(str(len(UMUGANDA_ACTIVITIES) + 1) + ". Type my own remark")

    choice = get_int_in_range(
        "Choose activity (1-" + str(len(UMUGANDA_ACTIVITIES) + 1) + "): ",
        1,
        len(UMUGANDA_ACTIVITIES) + 1
    )

    if choice == len(UMUGANDA_ACTIVITIES) + 1:
        custom = get_non_empty("Type Umuganda remark: ")
        return custom

    return UMUGANDA_ACTIVITIES[choice - 1]


def print_line(title=""):
    print("-" * 50)
    if title != "":
        print(title)
        print("-" * 50)


def success(message):
    print()
    print("✓", message)
    print()


def error(message):
    print()
    print("✗", message)
    print()


def tip(message):
    print("  Tip:", message)
