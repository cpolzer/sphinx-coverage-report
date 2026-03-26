# docs/conf.py
import os
from pathlib import Path

project = "sphinx-coverage-report"
author = "~christian polzer"
release = "0.1.0"

extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
]

html_theme = "furo"
needs_id_regex = ".*"
cr_rootdir = Path(__file__).parent
cr_warn_no_data = True
