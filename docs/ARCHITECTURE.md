# UmugandaSync — Architecture Notes

## Purpose

UmugandaSync helps village leaders coordinate community work: people,
attendance, projects, tools, and reporting.

## Runtime flow

1. `main.py` starts the session and language selection.
2. `login.py` authenticates an admin or member.
3. Admin users reach the dashboard + notification center, then the main menu.
4. Domain menus call into module files that query MySQL through `database.py`.

```
main.py
  └─ login.py
       └─ dashboard.py / notifications.py
            └─ menu.py
                 ├─ members.py
                 ├─ attendance.py
                 ├─ projects.py
                 ├─ tools.py
                 ├─ reports.py   ← Marvella
                 └─ search.py
```

## Data layer

- Engine: MySQL InnoDB (`database.sql`)
- Access: `database.run_query(sql, values=None, fetch=None)`
- Config: `config.py` with optional `UMUGANDA_DB_*` overrides

## Reports module design

`reports.py` separates:

1. Safe helpers (`safe_num`, `safe_row`)
2. Metric builders (`build_*`)
3. Console views
4. File exporters under `exports/`
5. `reports_menu()` orchestration

Builders are reusable by tests and future CSV/JSON exporters without
duplicating SQL.

## Module ownership

| Owner | Focus |
| --- | --- |
| Friend | Platform shell, login, dashboard, search, notifications |
| Rebecca | Database schema and connectivity |
| Joshua | Members |
| Cynthia | Attendance |
| Sonia | Projects |
| Rosette | Tools |
| Marvella | Reports and leader analytics docs |
## Demo surface

Leaders should open Reports after admin login for Marvella's presentation.
