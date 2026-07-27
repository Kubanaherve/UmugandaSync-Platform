# UmugandaSync Platform

Community work (Umuganda) management system for Rwandan villages.

Village leaders track members, attendance, projects, shared tools, and
operational reports from a single terminal application backed by MySQL.

## Problem Statement

Rwandan villages conduct monthly community work (Umuganda) every last Saturday.
Village leaders struggle to manually track attendance, manage community projects,
and coordinate shared tools across hundreds of members. Paper-based records get
lost, attendance is inconsistently reported, and project deadlines slip without
visibility. UmugandaSync digitises the entire workflow so leaders can:

- Register members with Rwanda National ID validation
- Record Umuganda attendance per session with present/late/absent/excused
- Manage community projects with progress tracking and deadline monitoring
- Track shared tool inventory (borrow/return, low-stock alerts)
- View a dashboard with real-time KPIs
- Generate and export reports (TXT/CSV) for leadership review

## Features

- **Dual role access**: Admin (full system) and Member (self-service view)
- **Multi-language**: English, French, Kinyarwanda
- **Member registry**: 16-digit Rwanda National ID PK, phone/email validation
- **Attendance tracking**: Per-session, roll call by village or all members
- **Project management**: CRUD, progress %, deadline monitoring, overdue alerts
- **Tool inventory**: Register, borrow, return, low-stock warnings
- **Dashboard**: Real-time community KPIs (members, attendance, projects, tools)
- **Notification center**: Low stock, overdue projects, absent members
- **Search**: By National ID, name, phone, email, project, tool, date
- **Reports & exports**: Community, member, attendance, project, inventory, KPI
- **CSV export**: Members, attendance, projects, tools to CSV files
- **Rate-limited login**: 3-attempt lockout for security

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

### Prerequisites

- Python 3.10+
- MySQL 8.0+ running locally or on a remote host

### Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd UmugandaSync-Platform

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Create the database
mysql -u root -p < database.sql

# 4. Configure database credentials (optional — defaults to root with no password)
#    Set environment variables or edit config.py:
#    export UMUGANDA_DB_HOST=localhost
#    export UMUGANDA_DB_USER=root
#    export UMUGANDA_DB_PASSWORD=yourpassword
#    export UMUGANDA_DB_NAME=umuganda_sync

# 5. Run the application
python3 main.py
```

### Demo credentials

**Admin**: `admin` / `admin123`

**Member**: NID `1199780123456789` / Phone `0788000001`

## Documentation

- [Installation](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User manual](docs/USER_MANUAL.md)
- [Testing](docs/TESTING.md)

## Development

```bash
# Syntax check all modules
python3 -m py_compile *.py

# Run tests
python3 -m unittest tests.py -v
```

## Tests

113+ unit tests covering validation, domain logic, database helpers, and reports.
Tests use mocking for the database layer so no MySQL connection is required.

## Team & Module Ownership

| Member | Role | Modules |
| --- | --- | --- |
| Friend Hervé | Platform lead | `main.py`, `login.py`, `menu.py`, `notifications.py`, `dashboard.py`, `search.py`, `helpers.py`, `languages.py`, `config.py` |
| Rebecca | Database | `database.py`, `database.sql` |
| Joshua | Members | `members.py` |
| Cynthia | Attendance | `attendance.py` |
| Sonia | Projects | `projects.py`, `csv_export.py` |
| Rosette | Tools | `tools.py` |
| Marvella | Reports & Docs | `reports.py`, `docs/` |

## License

Academic project — African Leadership University.
