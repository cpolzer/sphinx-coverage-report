# sphinxcontrib/coverage_report/environment.py
"""CSS static file injection for coverage report HTML output."""
import os
from sphinx.util import logging

logger = logging.getLogger(__name__)


def install_styles_static_files(app):
    """Copy the extension's CSS file to the Sphinx static output directory."""
    css_src = os.path.join(os.path.dirname(__file__), "css", "common.css")
    if not os.path.exists(css_src):
        return
    try:
        app.add_css_file("coverage_report_common.css")
    except Exception as exc:
        logger.debug("coverage-report: could not register CSS file: %s", exc)
