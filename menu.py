import logging
from typing import Optional

import languages
from helpers import input_with_exit

logger = logging.getLogger(__name__)


def show_login_header() -> None:
    print()
    print("=" * 56)
    print(languages.t("app_title"))
    print(languages.t("app_subtitle"))
    print("=" * 56)
    print()


def show_main_menu() -> None:
    items = [
        ("menu_members",),
        ("menu_attendance",),
        ("menu_projects",),
        ("menu_tools",),
        ("menu_reports",),
        ("menu_search",),
        ("menu_refresh",),
        ("menu_language",),
        ("menu_logout",),
        ("menu_exit",),
    ]
    build_menu(languages.t("main_menu"), items)


def get_choice(prompt_text: Optional[str] = None) -> str:
    if prompt_text is None:
        prompt_text = languages.t("enter_choice")
    return input_with_exit(prompt_text)


def build_menu(title: str, items: list[tuple], width: int = 44) -> None:
    print()
    print("-" * width)
    print(title)
    print("-" * width)
    for item in items:
        print(languages.t(item[0]))
    print("-" * width)
    logger.debug(f"Rendered menu: {title}")
