# UmugandaSync — Testing Guide

## Purpose

Verify platform modules compile and core logic behaves correctly before
presentation or deployment.

## Prerequisites

```bash
pip install -r requirements.txt
```

## Automated tests (no DB required)

113+ unit tests covering validation, domain logic, helpers, and reports:

```bash
python -m pytest tests.py -v
# or
python tests.py
```

### What is tested

| Module | Coverage |
|--------|----------|
| `config.py` | Constants and environment defaults |
| `database.py` | CRUD helpers, connection logic (mocked) |
| `members.py` | National ID, phone, email validation |
| `projects.py` | Validation, deadline labels, status derivation |
| `reports.py` | Metric builders, safe helpers (mocked) |
| `helpers.py` | Date formatting, sanitization, phone validation |
| `languages.py` | Translation resolution, key management |
| `search.py` | Quick search, national ID search |
| `login.py` | Admin and member login flows |
| `csv_export.py` | Export with mocked DB |
| `menu.py` | Menu rendering |

## Database connection test

```bash
python -c "import database; assert database.test_connection()"
```

### Aiven cloud connection

```bash
# Set your actual credentials (or copy .env.example to .env and edit)
export UMUGANDA_DB_HOST=your-project.aivencloud.com
export UMUGANDA_DB_PORT=11798
export UMUGANDA_DB_USER=avnadmin
export UMUGANDA_DB_PASSWORD=your_password_here
export UMUGANDA_DB_NAME=defaultdb
export UMUGANDA_DB_SSL_MODE=REQUIRED

python -c "import database; assert database.test_connection()"
```

## Full system smoke test

```bash
python main.py
```

1. Login as admin (`admin` / `admin123`)
2. Check dashboard shows data
3. Browse members, attendance, projects, tools
4. Run reports (menu option 5)
5. Try CSV export (menu option 5 then b)
6. Logout and test member login (ID=1 phone=0788000001)

## Failure triage

| Issue | Action |
|-------|--------|
| Connection failure | Check `.env` or `config.py` credentials |
| Empty reports | Run `database.sql` against the target DB |
| SSL error | Set `UMUGANDA_DB_SSL_MODE=REQUIRED` and `UMUGANDA_DB_SSL_CA=/path/to/ca.pem` |
| Export OSError | Ensure `exports/` is writable |
| Import errors | Run `pip install -r requirements.txt` |
