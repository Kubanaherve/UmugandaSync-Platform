# menu.py
# prints menus only — routing stays in main.py

import languages


def show_login_header():
    print()
    print("=" * 56)
    print(languages.t("app_title"))
    print(languages.t("app_subtitle"))
    print("=" * 56)
    print()


def show_main_menu():
    print()
    print("-" * 44)
    print(languages.t("main_menu"))
    print("-" * 44)
    print(languages.t("menu_members"))
    print(languages.t("menu_attendance"))
    print(languages.t("menu_projects"))
    print(languages.t("menu_tools"))
    print(languages.t("menu_reports"))
    print(languages.t("menu_search"))
    print(languages.t("menu_refresh"))
    print(languages.t("menu_language"))
    print(languages.t("menu_logout"))
    print(languages.t("menu_exit"))
    print("-" * 44)


def get_choice(prompt_text=None):
    if prompt_text == None:
        prompt_text = languages.t("enter_choice")
    choice = input(prompt_text)
    return choice.strip()

