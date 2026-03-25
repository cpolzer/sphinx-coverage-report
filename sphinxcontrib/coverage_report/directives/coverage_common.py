# sphinxcontrib/coverage_report/directives/coverage_common.py
import os
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger(__name__)


def _load_coverage_file(filepath, env):
    """Parse a coverage file and cache result in env.coveragereport_data."""
    if not hasattr(env, "coveragereport_data"):
        env.coveragereport_data = {}
    if filepath in env.coveragereport_data:
        return env.coveragereport_data[filepath]

    if not os.path.exists(filepath):
        return None

    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".xml",):
        from sphinxcontrib.coverage_report.coberturaparser import CoberturaParser
        data = CoberturaParser(filepath).parse()
    elif ext in (".info", ".lcov"):
        from sphinxcontrib.coverage_report.lcovparser import LcovParser
        data = LcovParser(filepath).parse()
    elif ext in (".json",):
        from sphinxcontrib.coverage_report.jsonparser import JsonParser
        data = JsonParser(filepath).parse()
    else:
        return None

    env.coveragereport_data[filepath] = data
    return data


class CoverageCommonDirective(SphinxDirective):
    def _resolve_path(self, raw_path):
        rootdir = self.config.cr_rootdir
        return os.path.join(rootdir, raw_path) if not os.path.isabs(raw_path) else raw_path

    def _warn_if_no_data(self, filepath, data, identifier=None):
        """Emit Sphinx build-time warnings via sphinx.util.logging when coverage data is absent.

        This does NOT produce warning nodes in the document — call this before returning
        a warning node from run() so both the build log and the rendered doc signal the problem.
        """
        if not self.config.cr_warn_no_data:
            return
        if not os.path.exists(filepath):
            logger.warning(
                "sphinx-coverage-report: coverage file not found: '%s'",
                filepath,
                location=self.get_location(),
            )
        elif data is None or not data.get("packages"):
            logger.warning(
                "sphinx-coverage-report: no coverage data in '%s'",
                filepath,
                location=self.get_location(),
            )
        elif identifier:
            logger.warning(
                "sphinx-coverage-report: no coverage data found for '%s' in '%s'",
                identifier,
                filepath,
                location=self.get_location(),
            )

    def get_location(self):
        return (self.env.docname, self.lineno)
