"""
Parses coverage.py JSON output (coverage >= 5.0) into the normalized data model.

Derived fields:
  report.line_rate  = totals.covered_lines / totals.num_statements
  report.branch_rate = totals.covered_branches / totals.num_branches
  module.name      = os.path.basename(filename key)
  module.line_rate = summary.percent_covered / 100
  function.hits    = len(executed_lines)
"""
import json
import os
from collections import defaultdict
from sphinxcontrib.coverage_report.exceptions import (
    CoverageReportFileNotFound,
    CoverageReportFileInvalid,
)


class JsonParser:
    """Parses coverage.py JSON output into the normalized coverage data model."""

    def __init__(self, json_path, encoding="utf-8"):
        """Load and parse the JSON file.

        Args:
            json_path: Path to coverage.json file.
            encoding: File encoding (default utf-8).

        Raises:
            CoverageReportFileNotFound: If file does not exist.
            CoverageReportFileInvalid: If file is not valid JSON.
        """
        if not os.path.exists(json_path):
            raise CoverageReportFileNotFound(f"File not found: {json_path}")
        self.json_path = json_path
        self.encoding = encoding
        try:
            with open(json_path, encoding=encoding) as fh:
                self._data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise CoverageReportFileInvalid(f"Cannot parse {json_path}: {exc}") from exc

    def parse(self):
        """Return normalized coverage report dict."""
        totals = self._data.get("totals", {})
        lv = totals.get("num_statements", 0)
        lc = totals.get("covered_lines", 0)
        bv = totals.get("num_branches", 0)
        bc = totals.get("covered_branches", 0)
        meta = self._data.get("meta", {})
        return {
            "line_rate": lc / lv if lv else 0.0,
            "branch_rate": bc / bv if bv else 0.0,
            "lines_valid": lv,
            "lines_covered": lc,
            "branches_valid": bv,
            "branches_covered": bc,
            "timestamp": meta.get("timestamp", ""),
            "version": meta.get("version", ""),
            "packages": self._parse_packages(),
        }

    def _parse_packages(self):
        """Group files by directory and return list of package dicts."""
        by_pkg = defaultdict(list)
        for filepath, data in self._data.get("files", {}).items():
            pkg = os.path.dirname(filepath) or "."
            by_pkg[pkg].append(self._parse_module(filepath, data))

        packages = []
        for pkg_name, mods in by_pkg.items():
            lv = sum(m["lines_valid"] for m in mods)
            lc = sum(m["lines_covered"] for m in mods)
            bv = sum(m["branches_valid"] for m in mods)
            bc = sum(m["branches_covered"] for m in mods)
            packages.append({
                "name": pkg_name,
                "line_rate": lc / lv if lv else 0.0,
                "branch_rate": bc / bv if bv else 0.0,
                "lines_valid": lv,
                "lines_covered": lc,
                "branches_valid": bv,
                "branches_covered": bc,
                "modules": mods,
            })
        return packages

    @staticmethod
    def _parse_module(filepath, data):
        """Parse a single file entry into a module dict."""
        summary = data.get("summary", {})
        lv = summary.get("num_statements", 0)
        lc = summary.get("covered_lines", 0)
        bv = summary.get("num_branches", 0)
        bc = summary.get("covered_branches", 0)
        pct = summary.get("percent_covered", 0.0)
        bpct = summary.get("percent_branches_covered", 0.0)
        functions = []
        for fn_name, fn_data in data.get("functions", {}).items():
            fn_summary = fn_data.get("summary", {})
            fn_statements = fn_summary.get("num_statements", 0)
            fn_covered = fn_summary.get("covered_lines", 0)
            functions.append({
                "name": fn_name,
                "line_start": fn_data.get("start_line", 0),
                "line_rate": fn_covered / fn_statements if fn_statements else 0.0,
                "hits": len(fn_data.get("executed_lines", [])),
            })
        return {
            "name": os.path.basename(filepath),
            "filename": filepath,
            "line_rate": pct / 100.0,
            "branch_rate": bpct / 100.0,
            "lines_valid": lv,
            "lines_covered": lc,
            "branches_valid": bv,
            "branches_covered": bc,
            "missed_lines": data.get("missing_lines", []),
            "complexity": 0.0,  # not in coverage.py JSON
            "functions": functions,
        }
