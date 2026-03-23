"""
Parses lcov .info files into the normalized coverage data model.

Key record types:
  TN: test name (ignored)        SF: source file path
  FN:<line>,<name>               FNDA:<count>,<name>
  FNF: functions found           FNH: functions hit
  BRDA:<line>,<block>,<br>,<hit> BRF: branches found   BRH: branches hit
  DA:<line>,<count>              LF: lines found        LH: lines hit
  end_of_record
"""
import os
from collections import defaultdict
from sphinxcontrib.coverage_report.exceptions import CoverageReportFileNotFound


class LcovParser:
    def __init__(self, lcov_path, encoding="utf-8"):
        if not os.path.exists(lcov_path):
            raise CoverageReportFileNotFound(f"File not found: {lcov_path}")
        self.lcov_path = lcov_path
        self.encoding = encoding

    def parse(self):
        modules_by_pkg = defaultdict(list)
        with open(self.lcov_path, encoding=self.encoding) as fh:
            current = self._empty_module()
            for raw in fh:
                line = raw.strip()
                if line.startswith("SF:"):
                    current["filename"] = line[3:]
                    current["name"] = os.path.basename(current["filename"])
                elif line.startswith("FN:"):
                    lineno, name = line[3:].split(",", 1)
                    current["_fn_lines"][name] = int(lineno)
                elif line.startswith("FNDA:"):
                    count, name = line[5:].split(",", 1)
                    current["_fn_hits"][name] = int(count)
                elif line.startswith("DA:"):
                    lineno, count = line[3:].split(",", 1)[:2]
                    current["_da"][int(lineno)] = int(count)
                elif line.startswith("BRF:"):
                    current["branches_valid"] = int(line[4:])
                elif line.startswith("BRH:"):
                    current["branches_covered"] = int(line[4:])
                elif line == "end_of_record":
                    self._finalize_module(current)
                    pkg = os.path.dirname(current["filename"]) or "."
                    modules_by_pkg[pkg].append(current)
                    current = self._empty_module()

        packages = []
        total_lv = total_lc = total_bv = total_bc = 0
        for pkg_name, mods in modules_by_pkg.items():
            pkg_lv = sum(m["lines_valid"] for m in mods)
            pkg_lc = sum(m["lines_covered"] for m in mods)
            pkg_bv = sum(m["branches_valid"] for m in mods)
            pkg_bc = sum(m["branches_covered"] for m in mods)
            total_lv += pkg_lv; total_lc += pkg_lc
            total_bv += pkg_bv; total_bc += pkg_bc
            packages.append({
                "name": pkg_name,
                "line_rate": pkg_lc / pkg_lv if pkg_lv else 0.0,
                "branch_rate": pkg_bc / pkg_bv if pkg_bv else 0.0,
                "lines_valid": pkg_lv, "lines_covered": pkg_lc,
                "branches_valid": pkg_bv, "branches_covered": pkg_bc,
                "modules": mods,
            })

        return {
            "line_rate": total_lc / total_lv if total_lv else 0.0,
            "branch_rate": total_bc / total_bv if total_bv else 0.0,
            "lines_valid": total_lv, "lines_covered": total_lc,
            "branches_valid": total_bv, "branches_covered": total_bc,
            "timestamp": "", "version": "",
            "packages": packages,
        }

    @staticmethod
    def _empty_module():
        return {
            "name": "", "filename": "",
            "line_rate": 0.0, "branch_rate": 0.0,
            "lines_valid": 0, "lines_covered": 0,
            "branches_valid": 0, "branches_covered": 0,
            "missed_lines": [], "complexity": 0.0, "functions": [],
            "_fn_lines": {}, "_fn_hits": {}, "_da": {},
        }

    @staticmethod
    def _finalize_module(m):
        da = m.pop("_da")
        fn_lines = m.pop("_fn_lines")
        fn_hits = m.pop("_fn_hits")
        m["lines_valid"] = len(da)
        m["lines_covered"] = sum(1 for h in da.values() if h > 0)
        m["missed_lines"] = sorted(ln for ln, h in da.items() if h == 0)
        m["line_rate"] = m["lines_covered"] / m["lines_valid"] if m["lines_valid"] else 0.0
        m["branch_rate"] = (
            m["branches_covered"] / m["branches_valid"]
            if m["branches_valid"] else 0.0
        )
        m["functions"] = [
            {
                "name": name,
                "line_start": fn_lines.get(name, 0),
                "line_rate": 1.0 if fn_hits.get(name, 0) > 0 else 0.0,
                "hits": fn_hits.get(name, 0),
            }
            for name in fn_lines
        ]
