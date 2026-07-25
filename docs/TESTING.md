# UmugandaSync — Testing Guide

## Purpose

Verify platform modules compile and the reports helpers behave correctly
before presentation or deployment.

## Quick checks

```bash
python3 -m py_compile *.py
python3 tests.py
```

## Reports checklist (manual)

With MySQL running and seed data loaded:

1. Login as admin
2. Open Reports
3. Run options 1–8; confirm numbers look sane vs dashboard
4. Run exports 9, 10, 12; confirm files appear in `exports/`
5. Run KPI snapshot (11)
6. Exit with 0 and confirm return to main menu

## Automated helper tests

`tests.py` covers shared utilities. Reports-specific pure helpers can be
checked quickly:

```bash
python3 - <<'PY'
import reports
assert reports.safe_num(None) == 0
assert reports.safe_num(5) == 5
assert reports.safe_row(None, "total") == 0
assert reports.safe_row({"total": None}, "total") == 0
assert reports.safe_row({"total": 3}, "total") == 3
print("reports helpers OK")
PY
```

## Database smoke test

```bash
python3 -c "import database; assert database.test_connection()"
```

## Failure triage

| Issue | Action |
| --- | --- |
| Connection failure | Fix `config.py` / start MySQL |
| Empty reports | Confirm `database.sql` seed applied |
| Export OSError | Ensure `exports/` is writable |
## Presentation smoke

Run options 1 and 13 once before presenting.
