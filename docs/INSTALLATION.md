# UmugandaSync — Installation Guide

## Requirements

- Python 3.10 or newer
- MySQL 8.x (local or remote)
- pip

## Setup

1. Clone the repository

```bash
git clone https://github.com/Kubanaherve/UmugandaSync-Platform.git
cd UmugandaSync-Platform
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create the database

```bash
mysql -u root -p < database.sql
```

This creates `umuganda_sync` with seed data for demos.

4. Configure connection

Edit `config.py` or set environment variables:

- `UMUGANDA_DB_HOST` (default `localhost`)
- `UMUGANDA_DB_USER` (default `root`)
- `UMUGANDA_DB_PASSWORD`
- `UMUGANDA_DB_NAME` (default `umuganda_sync`)

5. Run

```bash
python3 main.py
```

## Demo accounts

| Role | Credentials |
| --- | --- |
| Admin | username `admin` / password `admin123` |
| Member | Member ID `1` / phone `0788000001` |

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Access denied | MySQL user/password in `config.py` |
| Unknown database | Re-run `database.sql` |
| Module not found | Same Python env as `pip install` |
| Export failures | Writable `exports/` directory |

## Verify install

```bash
python3 -c "import database; print(database.test_connection())"
python3 tests.py
```
