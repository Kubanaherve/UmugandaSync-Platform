# UmugandaSync Platform

Community work (Umuganda) management for Rwandan villages.

Village leaders track members, attendance, projects, shared tools, and
operational reports from a single terminal application backed by MySQL.

## Features

- Admin and member login with language selection (EN / FR / RW)
- Member registry with Rwanda National ID validation
- Umuganda attendance tracking and village analytics
- Community project progress, deadlines, and completion
- Shared tool inventory and borrow history
- Notification center for low stock, absences, and overdue work
- Leader reports with on-screen summaries and file exports

## Architecture

| Layer | Modules |
| --- | --- |
| Entry / UX | `main.py`, `menu.py`, `login.py`, `languages.py`, `helpers.py` |
| Domain | `members.py`, `attendance.py`, `projects.py`, `tools.py` |
| Insights | `dashboard.py`, `notifications.py`, `search.py`, `reports.py` |
| Data | `database.py`, `database.sql`, `config.py` |
| Exports | `csv_export.py`, `exports/` |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module ownership and data flow.

## Quick start

1. Python 3.10+ and MySQL
2. `pip install -r requirements.txt`
3. `mysql -u root -p < database.sql`
4. Set credentials in `config.py` (or `UMUGANDA_DB_*` env vars)
5. `python3 main.py`

Default admin: `admin` / `admin123`

## Documentation

- [Installation](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User manual (Reports)](docs/USER_MANUAL.md)
- [Testing](docs/TESTING.md)

## Development

```bash
python3 -m py_compile *.py
python3 tests.py
```

## License

Academic project — African Leadership University.

## Reports owner

Reports module owned by Marvella (`marvella-reports` branch).
