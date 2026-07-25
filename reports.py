"""
reports.py
Owner: Marvella (mmarvellio77)

Production reporting and analytics for UmugandaSync village leaders.

Layers
------
1. Helpers / validation
2. Data access (parameterized SQL via database.run_query)
3. Metric builders (pure-ish aggregations)
4. Console presentation
5. File exports
6. Interactive menu

Public entrypoint used by main.py: ``reports_menu()``.

Production checklist covered by this module:
    - Community / member / attendance / project / inventory reports
    - Overdue project highlighting
    - KPI snapshot for leaders
    - Timestamped exports under ``exports/`` (TXT and CSV)
    - None-safe aggregates for empty tables
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from typing import Any, Optional

import database
import helpers
import languages

logger = logging.getLogger(__name__)

EXPORT_DIR = os.environ.get("UMUGANDA_CSV_DIR", "exports")
