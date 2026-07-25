# UmugandaSync — Installation Guide

## Requirements

- Python 3.10 or newer
- MySQL 8.x (local or remote, e.g. Aiven Cloud)
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

For **local MySQL**:
```bash
mysql -u root -p < database.sql
```

For **Aiven Cloud MySQL** (SSL required):
```bash
# Download CA certificate from Aiven console, save as ca.pem
mysql -u avnadmin -p \
  --host your-project.aivencloud.com \
  --port 11798 \
  --ssl-ca ca.pem \
  --ssl-mode REQUIRED \
  defaultdb < database.sql
```

4. Configure connection

Copy the example env file and edit it:
```bash
cp .env.example .env
```

Edit `.env` with your connection details:

### Local MySQL
```
UMUGANDA_DB_HOST=localhost
UMUGANDA_DB_PORT=3306
UMUGANDA_DB_USER=root
UMUGANDA_DB_PASSWORD=your_password
UMUGANDA_DB_NAME=umuganda_sync
```

### Aiven Cloud MySQL
```
UMUGANDA_DB_HOST=your-project.aivencloud.com
UMUGANDA_DB_PORT=11798
UMUGANDA_DB_USER=avnadmin
UMUGANDA_DB_PASSWORD=your_password_here
UMUGANDA_DB_NAME=defaultdb
UMUGANDA_DB_SSL_MODE=REQUIRED
UMUGANDA_DB_SSL_CA=ca.pem
```

5. Run

```bash
python3 main.py
```

## Demo accounts

| Role | Credentials |
|------|------------|
| Admin | username `admin` / password `admin123` |
| Member | Member ID `1` / phone `0788000001` |

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Access denied | MySQL user/password in `.env` |
| Unknown database | Re-run `database.sql` |
| SSL connection error | Set `UMUGANDA_DB_SSL_MODE=REQUIRED` and `UMUGANDA_DB_SSL_CA` |
| Module not found | Same Python env as `pip install` |
| Export failures | Writable `exports/` directory |

## Verify install

```bash
python3 -c "import database; print(database.test_connection())"
python3 -m pytest tests.py -v
```
