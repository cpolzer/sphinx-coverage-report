# sphinx-coverage-report Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Sphinx extension that parses Cobertura XML, lcov, and JSON coverage reports and renders them as sphinx-needs need nodes and standalone tables, with threshold-based status and cross-linking to sphinx-test-reports.

**Architecture:** Three format-specific parsers (Cobertura, lcov, JSON) all normalize to the same Python dict shape. Six directives consume the parsed data — one standalone table (`coverage-results`) and five sphinx-needs node types (`coverage-report`, `coverage-package`, `coverage-module`, `coverage-function`). A `cr_link()` dynamic function enables cross-linking to test-case nodes from sphinx-test-reports.

**Tech Stack:** Python 3.10+, Sphinx > 4.0, sphinx-needs >= 6.0.0, lxml, packaging, pytest, nox.

---

## File Map

### New files to create

```
sphinxcontrib/coverage_report/
├── __init__.py                          # re-exports setup()
├── coverage_report.py                   # setup(), config values, shim, event hooks
├── coberturaparser.py                   # Parses coverage.xml → normalized dicts
├── lcovparser.py                        # Parses lcov.info → normalized dicts
├── jsonparser.py                        # Parses coverage.json → normalized dicts
├── config.py                            # DEFAULT_OPTIONS list, threshold helpers
├── environment.py                       # CSS static file injection
├── exceptions.py                        # CoverageReportFileNotFound etc.
├── directives/
│   ├── __init__.py
│   ├── coverage_common.py               # Base directive: file loading, ID gen, threshold, warnings
│   ├── coverage_results.py              # Standalone table (no sphinx-needs)
│   ├── coverage_report_directive.py     # Template-expanded full report
│   ├── coverage_package.py              # Need node per package
│   ├── coverage_module.py               # Need node per source file
│   ├── coverage_function.py             # Need node per function/method
│   └── coverage_report_template.txt     # Default RST template
├── functions/
│   └── __init__.py                      # cr_link() dynamic function
└── schemas/
    └── cobertura.xsd                    # Cobertura XML schema (copy/adapt from spec)

tests/
├── conftest.py
├── fixtures/
│   ├── coverage.xml                     # Cobertura XML fixture
│   ├── coverage_empty.xml               # Cobertura with zero data
│   ├── lcov.info                        # lcov fixture
│   └── coverage.json                    # coverage.py JSON fixture
├── doc_test/
│   ├── basic_results/                   # coverage-results directive Sphinx test project
│   │   ├── conf.py
│   │   ├── index.rst
│   │   └── (symlink or copy of fixture)
│   ├── module_needs/                    # coverage-module directive Sphinx test project
│   │   ├── conf.py
│   │   └── index.rst
│   └── full_report/                     # coverage-report directive Sphinx test project
│       ├── conf.py
│       └── index.rst
├── test_cobertura_parser.py
├── test_lcov_parser.py
├── test_json_parser.py
├── test_coverage_results.py
├── test_coverage_module.py
├── test_threshold_status.py
├── test_warnings.py
└── test_cr_link.py

pyproject.toml
noxfile.py
.github/workflows/ci.yaml
```

---

## Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `sphinxcontrib/__init__.py` (namespace package — empty)
- Create: `sphinxcontrib/coverage_report/__init__.py`
- Create: `sphinxcontrib/coverage_report/exceptions.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create the namespace package marker**

```python
# sphinxcontrib/__init__.py  — must be empty (PEP 420 namespace package)
```

```python
# sphinxcontrib/coverage_report/__init__.py
from sphinxcontrib.coverage_report.coverage_report import setup

__all__ = ["setup"]
```

- [ ] **Step 2: Create exceptions**

```python
# sphinxcontrib/coverage_report/exceptions.py
class CoverageReportError(Exception):
    pass

class CoverageReportFileNotFound(CoverageReportError):
    pass

class CoverageReportFileInvalid(CoverageReportError):
    pass

class CoverageReportInvalidOption(CoverageReportError):
    pass
```

- [ ] **Step 3: Create pyproject.toml**

```toml
[build-system]
requires = ["flit_core>=3.2"]
build-backend = "flit_core.buildapi"

[project]
name = "sphinx-coverage-report"
version = "0.1.0"
description = "Sphinx extension for showing code coverage results"
readme = "README.rst"
requires-python = ">=3.10"
license = {text = "MIT"}
dependencies = [
    "sphinx>4.0",
    "lxml",
    "sphinx-needs>=6.0.0",
    "packaging",
]

[project.optional-dependencies]
test = [
    "nox>=2025.2.9",
    "pytest>=7.0",
    "pytest-cov",
    "pytest-xdist",
]

[tool.flit.module]
name = "sphinxcontrib.coverage_report"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Create conftest.py**

```python
# tests/conftest.py
import os
import pytest

@pytest.fixture
def fixture_dir():
    return os.path.join(os.path.dirname(__file__), "fixtures")
```

- [ ] **Step 5: Install in dev mode and verify import**

```bash
pip install -e ".[test]"
python -c "import sphinxcontrib.coverage_report; print('ok')"
```
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml sphinxcontrib/ tests/conftest.py
git commit -m "chore: project scaffolding — namespace package, exceptions, pyproject.toml"
```

---

## Task 2: Cobertura XML parser

**Files:**
- Create: `sphinxcontrib/coverage_report/coberturaparser.py`
- Create: `tests/fixtures/coverage.xml`
- Create: `tests/test_cobertura_parser.py`

- [ ] **Step 1: Create the fixture file**

```xml
<!-- tests/fixtures/coverage.xml -->
<?xml version="1.0" ?>
<coverage version="7.4.0" timestamp="1711180800" lines-valid="100"
          lines-covered="87" line-rate="0.87" branches-covered="30"
          branches-valid="40" branch-rate="0.75" complexity="0">
    <packages>
        <package name="mypackage" line-rate="0.91" branch-rate="0.80"
                 complexity="1.5">
            <classes>
                <class name="module.py" filename="mypackage/module.py"
                       line-rate="0.92" branch-rate="0.85" complexity="2.1">
                    <methods/>
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="5" hits="1"/>
                        <line number="10" hits="0"/>
                        <line number="15" hits="1"/>
                        <line number="20" hits="0" branch="true"
                              condition-coverage="50% (1/2)"/>
                    </lines>
                </class>
                <class name="utils.py" filename="mypackage/utils.py"
                       line-rate="0.80" branch-rate="0.70" complexity="1.0">
                    <methods/>
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="3" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_cobertura_parser.py
import os
import pytest
from sphinxcontrib.coverage_report.coberturaparser import CoberturaParser
from sphinxcontrib.coverage_report.exceptions import CoverageReportFileNotFound

@pytest.fixture
def parser(fixture_dir):
    return CoberturaParser(os.path.join(fixture_dir, "coverage.xml"))

def test_file_not_found_raises():
    with pytest.raises(CoverageReportFileNotFound):
        CoberturaParser("/nonexistent/coverage.xml")

def test_parse_returns_report_shape(parser):
    result = parser.parse()
    assert result["line_rate"] == pytest.approx(0.87)
    assert result["branch_rate"] == pytest.approx(0.75)
    assert result["lines_valid"] == 100
    assert result["lines_covered"] == 87
    assert result["branches_valid"] == 40
    assert result["branches_covered"] == 30
    assert "timestamp" in result
    assert "version" in result
    assert len(result["packages"]) == 1

def test_parse_package_shape(parser):
    pkg = parser.parse()["packages"][0]
    assert pkg["name"] == "mypackage"
    assert pkg["line_rate"] == pytest.approx(0.91)
    assert len(pkg["modules"]) == 2

def test_parse_module_shape(parser):
    mod = parser.parse()["packages"][0]["modules"][0]
    assert mod["name"] == "module.py"
    assert mod["filename"] == "mypackage/module.py"
    assert mod["line_rate"] == pytest.approx(0.92)
    assert 10 in mod["missed_lines"]
    assert 20 in mod["missed_lines"]

def test_parse_module_functions_empty_for_cobertura(parser):
    # Cobertura does not carry function-level data
    mod = parser.parse()["packages"][0]["modules"][0]
    assert mod["functions"] == []
```

- [ ] **Step 3: Run to confirm they fail**

```bash
pytest tests/test_cobertura_parser.py -v
```
Expected: all tests FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 4: Implement CoberturaParser**

```python
# sphinxcontrib/coverage_report/coberturaparser.py
import os
from lxml import etree
from sphinxcontrib.coverage_report.exceptions import (
    CoverageReportFileNotFound,
    CoverageReportFileInvalid,
)


class CoberturaParser:
    def __init__(self, xml_path, xsd_path=None):
        if not os.path.exists(xml_path):
            raise CoverageReportFileNotFound(f"File not found: {xml_path}")
        self.xml_path = xml_path
        self.xsd_path = xsd_path or os.path.join(
            os.path.dirname(__file__), "schemas", "cobertura.xsd"
        )
        self._doc = etree.parse(xml_path)

    def validate(self):
        if not os.path.exists(self.xsd_path):
            return True  # schema optional
        schema = etree.XMLSchema(etree.parse(self.xsd_path))
        return schema.validate(self._doc)

    def parse(self):
        root = self._doc.getroot()
        return {
            "line_rate": float(root.get("line-rate", 0)),
            "branch_rate": float(root.get("branch-rate", 0)),
            "lines_valid": int(root.get("lines-valid", 0)),
            "lines_covered": int(root.get("lines-covered", 0)),
            "branches_valid": int(root.get("branches-valid", 0)),
            "branches_covered": int(root.get("branches-covered", 0)),
            "timestamp": root.get("timestamp", ""),
            "version": root.get("version", ""),
            "packages": self._parse_packages(root),
        }

    def _parse_packages(self, root):
        packages = []
        for pkg in root.findall(".//package"):
            classes = pkg.findall(".//class")
            modules = []
            lines_valid = lines_covered = branches_valid = branches_covered = 0
            for cls in classes:
                mod = self._parse_class(cls)
                modules.append(mod)
                lines_valid += mod["lines_valid"]
                lines_covered += mod["lines_covered"]
                branches_valid += mod["branches_valid"]
                branches_covered += mod["branches_covered"]
            packages.append({
                "name": pkg.get("name", ""),
                "line_rate": float(pkg.get("line-rate", 0)),
                "branch_rate": float(pkg.get("branch-rate", 0)),
                "lines_valid": lines_valid,
                "lines_covered": lines_covered,
                "branches_valid": branches_valid,
                "branches_covered": branches_covered,
                "modules": modules,
            })
        return packages

    def _parse_class(self, cls):
        missed = []
        lines_valid = lines_covered = branches_valid = branches_covered = 0
        for line in cls.findall(".//line"):
            lines_valid += 1
            hits = int(line.get("hits", 0))
            number = int(line.get("number", 0))
            if hits == 0:
                missed.append(number)
            else:
                lines_covered += 1
            if line.get("branch") == "true":
                cc = line.get("condition-coverage", "")
                try:
                    covered, total = cc.split("(")[1].rstrip(")").split("/")
                    branches_covered += int(covered)
                    branches_valid += int(total)
                except (IndexError, ValueError):
                    pass
        return {
            "name": cls.get("name", ""),
            "filename": cls.get("filename", ""),
            "line_rate": float(cls.get("line-rate", 0)),
            "branch_rate": float(cls.get("branch-rate", 0)),
            "lines_valid": lines_valid,
            "lines_covered": lines_covered,
            "branches_valid": branches_valid,
            "branches_covered": branches_covered,
            "missed_lines": missed,
            "complexity": float(cls.get("complexity", 0)),
            "functions": [],  # Cobertura does not carry function-level data
        }
```

- [ ] **Step 5: Run tests to confirm pass**

```bash
pytest tests/test_cobertura_parser.py -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add sphinxcontrib/coverage_report/coberturaparser.py tests/fixtures/coverage.xml tests/test_cobertura_parser.py
git commit -m "feat: CoberturaParser — parse coverage.xml to normalized dicts"
```

---

## Task 3: lcov parser

**Files:**
- Create: `sphinxcontrib/coverage_report/lcovparser.py`
- Create: `tests/fixtures/lcov.info`
- Create: `tests/test_lcov_parser.py`

- [ ] **Step 1: Create the lcov fixture**

```
# tests/fixtures/lcov.info
TN:
SF:mypackage/module.py
FN:10,my_function
FN:30,another_function
FNDA:5,my_function
FNDA:0,another_function
FNF:2
FNH:1
BRDA:20,0,0,1
BRDA:20,0,1,0
BRF:2
BRH:1
DA:1,1
DA:5,1
DA:10,0
DA:15,1
DA:20,1
LF:5
LH:4
end_of_record
TN:
SF:mypackage/utils.py
FNF:0
FNH:0
BRF:0
BRH:0
DA:1,1
DA:3,0
LF:2
LH:1
end_of_record
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_lcov_parser.py
import os
import pytest
from sphinxcontrib.coverage_report.lcovparser import LcovParser
from sphinxcontrib.coverage_report.exceptions import CoverageReportFileNotFound

@pytest.fixture
def parser(fixture_dir):
    return LcovParser(os.path.join(fixture_dir, "lcov.info"))

def test_file_not_found_raises():
    with pytest.raises(CoverageReportFileNotFound):
        LcovParser("/nonexistent/lcov.info")

def test_parse_report_aggregates(parser):
    result = parser.parse()
    assert result["lines_valid"] == 7
    assert result["lines_covered"] == 5
    assert result["line_rate"] == pytest.approx(5 / 7)
    assert result["branches_valid"] == 2
    assert result["branches_covered"] == 1
    assert len(result["packages"]) == 1

def test_parse_module_shape(parser):
    pkg = parser.parse()["packages"][0]
    assert pkg["name"] == "mypackage"
    mod = pkg["modules"][0]
    assert mod["filename"] == "mypackage/module.py"
    assert mod["lines_valid"] == 5
    assert mod["lines_covered"] == 4
    assert 10 in mod["missed_lines"]

def test_parse_functions(parser):
    mod = parser.parse()["packages"][0]["modules"][0]
    assert len(mod["functions"]) == 2
    fn = next(f for f in mod["functions"] if f["name"] == "my_function")
    assert fn["hits"] == 5
    assert fn["line_start"] == 10
    fn2 = next(f for f in mod["functions"] if f["name"] == "another_function")
    assert fn2["hits"] == 0
```

- [ ] **Step 3: Run to confirm they fail**

```bash
pytest tests/test_lcov_parser.py -v
```
Expected: FAIL

- [ ] **Step 4: Implement LcovParser**

```python
# sphinxcontrib/coverage_report/lcovparser.py
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
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_lcov_parser.py -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add sphinxcontrib/coverage_report/lcovparser.py tests/fixtures/lcov.info tests/test_lcov_parser.py
git commit -m "feat: LcovParser — parse lcov.info to normalized dicts"
```

---

## Task 4: JSON parser

**Files:**
- Create: `sphinxcontrib/coverage_report/jsonparser.py`
- Create: `tests/fixtures/coverage.json`
- Create: `tests/test_json_parser.py`

- [ ] **Step 1: Create the JSON fixture**

```json
{
    "meta": {
        "version": "7.4.0",
        "timestamp": "2026-03-23T10:00:00",
        "branch_coverage": true,
        "show_contexts": false
    },
    "files": {
        "mypackage/module.py": {
            "executed_lines": [1, 5, 15, 20],
            "summary": {
                "covered_lines": 4,
                "num_statements": 5,
                "percent_covered": 80.0,
                "percent_covered_display": "80%",
                "missing_lines": 1,
                "excluded_lines": 0,
                "num_branches": 2,
                "covered_branches": 1,
                "percent_branches_covered": 50.0
            },
            "missing_lines": [10],
            "excluded_lines": [],
            "functions": {
                "my_function": {
                    "start_line": 10,
                    "executed_lines": [10, 15],
                    "summary": {
                        "covered_lines": 2,
                        "num_statements": 3
                    },
                    "missing_lines": [12]
                }
            }
        },
        "mypackage/utils.py": {
            "executed_lines": [1],
            "summary": {
                "covered_lines": 1,
                "num_statements": 2,
                "percent_covered": 50.0,
                "percent_covered_display": "50%",
                "missing_lines": 1,
                "excluded_lines": 0,
                "num_branches": 0,
                "covered_branches": 0,
                "percent_branches_covered": 0.0
            },
            "missing_lines": [3],
            "excluded_lines": [],
            "functions": {}
        }
    },
    "totals": {
        "covered_lines": 5,
        "num_statements": 7,
        "percent_covered": 71.43,
        "percent_covered_display": "71%",
        "missing_lines": 2,
        "excluded_lines": 0,
        "num_branches": 2,
        "covered_branches": 1,
        "percent_branches_covered": 50.0
    }
}
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_json_parser.py
import os
import pytest
from sphinxcontrib.coverage_report.jsonparser import JsonParser
from sphinxcontrib.coverage_report.exceptions import CoverageReportFileNotFound

@pytest.fixture
def parser(fixture_dir):
    return JsonParser(os.path.join(fixture_dir, "coverage.json"))

def test_file_not_found_raises():
    with pytest.raises(CoverageReportFileNotFound):
        JsonParser("/nonexistent/coverage.json")

def test_parse_report_totals(parser):
    result = parser.parse()
    assert result["lines_valid"] == 7
    assert result["lines_covered"] == 5
    assert result["line_rate"] == pytest.approx(5 / 7)
    assert result["branches_valid"] == 2
    assert result["branches_covered"] == 1
    assert result["version"] == "7.4.0"

def test_parse_groups_by_package(parser):
    result = parser.parse()
    assert len(result["packages"]) == 1
    assert result["packages"][0]["name"] == "mypackage"

def test_parse_module_shape(parser):
    mod = parser.parse()["packages"][0]["modules"][0]
    assert mod["filename"] == "mypackage/module.py"
    assert mod["name"] == "module.py"
    assert mod["line_rate"] == pytest.approx(0.80)
    assert mod["missed_lines"] == [10]

def test_parse_function_shape(parser):
    mod = parser.parse()["packages"][0]["modules"][0]
    assert len(mod["functions"]) == 1
    fn = mod["functions"][0]
    assert fn["name"] == "my_function"
    assert fn["line_start"] == 10
    assert fn["hits"] == 2  # len(executed_lines)
```

- [ ] **Step 3: Run to confirm they fail**

```bash
pytest tests/test_json_parser.py -v
```
Expected: FAIL

- [ ] **Step 4: Implement JsonParser**

```python
# sphinxcontrib/coverage_report/jsonparser.py
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
from sphinxcontrib.coverage_report.exceptions import CoverageReportFileNotFound


class JsonParser:
    def __init__(self, json_path, mapping=None, encoding="utf-8"):
        if not os.path.exists(json_path):
            raise CoverageReportFileNotFound(f"File not found: {json_path}")
        self.json_path = json_path
        self.encoding = encoding
        with open(json_path, encoding=encoding) as fh:
            self._data = json.load(fh)

    def parse(self):
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
                "lines_valid": lv, "lines_covered": lc,
                "branches_valid": bv, "branches_covered": bc,
                "modules": mods,
            })
        return packages

    @staticmethod
    def _parse_module(filepath, data):
        summary = data.get("summary", {})
        lv = summary.get("num_statements", 0)
        lc = summary.get("covered_lines", 0)
        bv = summary.get("num_branches", 0)
        bc = summary.get("covered_branches", 0)
        pct = summary.get("percent_covered", 0.0)
        bpct = summary.get("percent_branches_covered", 0.0)
        functions = []
        for fn_name, fn_data in data.get("functions", {}).items():
            functions.append({
                "name": fn_name,
                "line_start": fn_data.get("start_line", 0),
                "line_rate": 1.0 if fn_data.get("executed_lines") else 0.0,
                "hits": len(fn_data.get("executed_lines", [])),
            })
        return {
            "name": os.path.basename(filepath),
            "filename": filepath,
            "line_rate": pct / 100.0,
            "branch_rate": bpct / 100.0,
            "lines_valid": lv, "lines_covered": lc,
            "branches_valid": bv, "branches_covered": bc,
            "missed_lines": data.get("missing_lines", []),
            "complexity": 0.0,  # not in coverage.py JSON
            "functions": functions,
        }
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_json_parser.py -v
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add sphinxcontrib/coverage_report/jsonparser.py tests/fixtures/coverage.json tests/test_json_parser.py
git commit -m "feat: JsonParser — parse coverage.py JSON to normalized dicts"
```

---

## Task 5: Extension setup and configuration

**Files:**
- Create: `sphinxcontrib/coverage_report/config.py`
- Create: `sphinxcontrib/coverage_report/environment.py`
- Create: `sphinxcontrib/coverage_report/coverage_report.py`
- Create: `sphinxcontrib/coverage_report/directives/__init__.py`

- [ ] **Step 1: Create config.py**

```python
# sphinxcontrib/coverage_report/config.py
"""Default option lists and threshold helpers."""

DEFAULT_OPTIONS = [
    "line_rate", "branch_rate", "lines_valid", "lines_covered",
    "branches_valid", "branches_covered", "missed_lines",
    "filename", "package", "complexity", "hits", "line_start",
]


def compute_status(data, app_config, level="module"):
    """Return 'passing' or 'failing' based on threshold config."""
    per_level = getattr(app_config, f"cr_threshold_{level}", {})
    line_threshold = per_level.get(
        "line_rate", app_config.cr_threshold_line_rate
    )
    branch_threshold = per_level.get(
        "branch_rate", app_config.cr_threshold_branch_rate
    )
    if data.get("line_rate", 1.0) < line_threshold:
        return "failing"
    bv = data.get("branches_valid", 0)
    if bv > 0 and data.get("branch_rate", 1.0) < branch_threshold:
        return "failing"
    return "passing"
```

- [ ] **Step 2: Create environment.py**

```python
# sphinxcontrib/coverage_report/environment.py
import os
from sphinx.util import logging

logger = logging.getLogger(__name__)


def install_styles_static_files(app):
    css_src = os.path.join(os.path.dirname(__file__), "css", "common.css")
    if not os.path.exists(css_src):
        return
    try:
        app.add_css_file("coverage_report_common.css")
    except Exception:
        pass
```

- [ ] **Step 3: Create coverage_report.py (setup + shim)**

The shim pattern is copied directly from sphinx-test-reports. The `coverage_report.py` registers all config values, need types, extra options, and event hooks.

```python
# sphinxcontrib/coverage_report/coverage_report.py
import os
import sphinx_needs
from packaging.version import Version
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx_needs.api import add_dynamic_function, add_need_type

try:
    from sphinx_needs.api import add_field as _add_field
    def _register_field(app, name, schema=None):
        _add_field(name, name, schema=schema)
except ImportError:
    from sphinx_needs.api import add_extra_option as _add_extra_option
    def _register_field(app, name, schema=None):
        _add_extra_option(app, name, **({} if schema is None else {"schema": schema}))

from sphinx.util import logging
from sphinxcontrib.coverage_report.functions import cr_link
from sphinxcontrib.coverage_report.environment import install_styles_static_files

logger = logging.getLogger(__name__)

VERSION = "0.1.0"

_DEFAULT_JSON_MAPPING = {
    "json_config": {
        "report": {
            "line_rate": ([], "0"),
            "branch_rate": ([], "0"),
            "lines_valid": (["totals", "num_statements"], "0"),
            "lines_covered": (["totals", "covered_lines"], "0"),
            "branches_valid": (["totals", "num_branches"], "0"),
            "branches_covered": (["totals", "covered_branches"], "0"),
            "timestamp": (["meta", "timestamp"], "unknown"),
            "version": (["meta", "version"], "unknown"),
        },
        "module": {
            "name": ([], "unknown"),
            "filename": ([], "unknown"),
            "line_rate": (["summary", "percent_covered"], "0"),
            "branch_rate": (["summary", "percent_branches_covered"], "0"),
            "lines_valid": (["summary", "num_statements"], "0"),
            "lines_covered": (["summary", "covered_lines"], "0"),
            "branches_valid": (["summary", "num_branches"], 0),
            "branches_covered": (["summary", "covered_branches"], 0),
            "missed_lines": (["missing_lines"], []),
        },
        "function": {
            "name": ([], "unknown"),
            "line_start": (["start_line"], 0),
            "hits": ([], 0),
        },
    }
}

_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "directives", "coverage_report_template.txt"
)


def setup(app: Sphinx):
    app.add_config_value("cr_rootdir", app.confdir, "html")
    app.add_config_value("cr_import_encoding", "utf-8", "html")
    app.add_config_value("cr_extra_options", [], "env")
    app.add_config_value("cr_warn_no_data", True, "html")

    app.add_config_value(
        "cr_report",
        ["coverage-report", "coveragereport", "Coverage Report", "CR_", "#4a90d9", "node"],
        "html",
    )
    app.add_config_value(
        "cr_package",
        ["coverage-package", "coveragepackage", "Coverage Package", "CP_", "#7ab648", "folder"],
        "html",
    )
    app.add_config_value(
        "cr_module",
        ["coverage-module", "coveragemodule", "Coverage Module", "CM_", "#f0ad4e", "rectangle"],
        "html",
    )
    app.add_config_value(
        "cr_function",
        ["coverage-function", "coveragefunction", "Coverage Function", "CF_", "#cccccc", "rectangle"],
        "html",
    )

    app.add_config_value("cr_threshold_line_rate", 0.80, "html")
    app.add_config_value("cr_threshold_branch_rate", 0.75, "html")
    app.add_config_value("cr_threshold_report", {}, "html")
    app.add_config_value("cr_threshold_package", {}, "html")
    app.add_config_value("cr_threshold_module", {}, "html")
    app.add_config_value("cr_module_id_length", 5, "html")
    app.add_config_value("cr_package_id_length", 3, "html")
    app.add_config_value("cr_json_mapping", _DEFAULT_JSON_MAPPING, "html", types=[dict])
    app.add_config_value("cr_report_template", _TEMPLATE_PATH, "html")

    app.connect("config-inited", _sphinx_needs_update)
    app.connect("builder-inited", install_styles_static_files)

    return {"version": VERSION, "parallel_read_safe": True}


def _sphinx_needs_update(app: Sphinx, config: Config) -> None:
    needs_version = Version(sphinx_needs.__version__)
    use_schema = needs_version >= Version("6.0.0")

    if use_schema:
        _register_field(app, "line_rate",        schema={"type": "number"})
        _register_field(app, "branch_rate",      schema={"type": "number"})
        _register_field(app, "lines_valid",      schema={"type": "integer"})
        _register_field(app, "lines_covered",    schema={"type": "integer"})
        _register_field(app, "branches_valid",   schema={"type": "integer"})
        _register_field(app, "branches_covered", schema={"type": "integer"})
        _register_field(app, "missed_lines",     schema={"type": "string"})
        _register_field(app, "filename",         schema={"type": "string"})
        _register_field(app, "package",          schema={"type": "string"})
        _register_field(app, "complexity",       schema={"type": "number"})
        _register_field(app, "hits",             schema={"type": "integer"})
        _register_field(app, "line_start",       schema={"type": "integer"})
        for opt in config.cr_extra_options:
            _register_field(app, opt, schema={"type": "string"})
    else:
        for field in [
            "line_rate", "branch_rate", "lines_valid", "lines_covered",
            "branches_valid", "branches_covered", "missed_lines",
            "filename", "package", "complexity", "hits", "line_start",
        ] + list(config.cr_extra_options):
            _register_field(app, field)

    add_dynamic_function(app, cr_link)
    add_need_type(app, *config.cr_report[1:])
    add_need_type(app, *config.cr_package[1:])
    add_need_type(app, *config.cr_module[1:])
    add_need_type(app, *config.cr_function[1:])
```

- [ ] **Step 4: Create directives/__init__.py (empty)**

```python
# sphinxcontrib/coverage_report/directives/__init__.py
```

- [ ] **Step 5: Create the functions stub so import works**

```python
# sphinxcontrib/coverage_report/functions/__init__.py
def cr_link(app, need, needs, option, filter_string=None, **kwargs):
    """Stub — implemented in Task 9."""
    return []
```

- [ ] **Step 6: Verify setup() can be imported cleanly**

```bash
python -c "from sphinxcontrib.coverage_report import setup; print('setup ok')"
```
Expected: `setup ok`

- [ ] **Step 7: Commit**

```bash
git add sphinxcontrib/coverage_report/
git commit -m "feat: extension setup, config values, sphinx-needs shim"
```

---

## Task 6: Standalone coverage-results directive

The `coverage-results` directive renders a simple docutils table — **no sphinx-needs dependency**. It's the fastest way to get visible output and validates the parser integration end-to-end.

**Files:**
- Create: `sphinxcontrib/coverage_report/directives/coverage_common.py`
- Create: `sphinxcontrib/coverage_report/directives/coverage_results.py`
- Create: `tests/doc_test/basic_results/conf.py`
- Create: `tests/doc_test/basic_results/index.rst`
- Create: `tests/test_coverage_results.py`

- [ ] **Step 1: Create coverage_common.py base class**

```python
# sphinxcontrib/coverage_report/directives/coverage_common.py
import os
from docutils.parsers.rst import Directive
from sphinx.util import logging

logger = logging.getLogger(__name__)


def _load_coverage_file(filepath, app):
    """Parse a coverage file and cache result in app.coveragereport_data."""
    if not hasattr(app, "coveragereport_data"):
        app.coveragereport_data = {}
    if filepath in app.coveragereport_data:
        return app.coveragereport_data[filepath]

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

    app.coveragereport_data[filepath] = data
    return data


class CoverageCommonDirective(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = self.state.document.settings.env
        self.app = self.env.app

    def _resolve_path(self, raw_path):
        rootdir = self.app.config.cr_rootdir
        return os.path.join(rootdir, raw_path) if not os.path.isabs(raw_path) else raw_path

    def _warn_if_no_data(self, filepath, data, identifier=None):
        if not self.app.config.cr_warn_no_data:
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
```

- [ ] **Step 2: Create coverage_results.py**

```python
# sphinxcontrib/coverage_report/directives/coverage_results.py
from docutils import nodes
from docutils.parsers.rst import directives
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective, _load_coverage_file,
)


class CoverageResultsDirective(CoverageCommonDirective):
    """
    Standalone coverage table. No sphinx-needs dependency.

    Usage::

        .. coverage-results:: path/to/coverage.xml
    """
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "package": directives.unchanged,
    }

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.app)

        if data is None or not data.get("packages"):
            self._warn_if_no_data(filepath, data)
            return [nodes.warning(
                "",
                nodes.paragraph(text=f"No coverage data available from: {filepath}"),
            )]

        pkg_filter = self.options.get("package")
        modules = []
        for pkg in data["packages"]:
            if pkg_filter and pkg["name"] != pkg_filter:
                continue
            modules.extend(pkg["modules"])

        return [self._build_table(modules)]

    def _build_table(self, modules):
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup
        for width in [40, 20, 20, 20]:
            tgroup += nodes.colspec(colwidth=width)

        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for title in ["Module", "Line Rate", "Branch Rate", "Missed Lines"]:
            entry = nodes.entry()
            entry += nodes.paragraph(text=title)
            header_row += entry
        thead += header_row

        tbody = nodes.tbody()
        tgroup += tbody
        for mod in modules:
            row = nodes.row()
            for val in [
                mod["filename"],
                f"{mod['line_rate']:.0%}",
                f"{mod['branch_rate']:.0%}" if mod["branches_valid"] else "n/a",
                ", ".join(str(l) for l in mod["missed_lines"]) or "—",
            ]:
                entry = nodes.entry()
                entry += nodes.paragraph(text=val)
                row += entry
            tbody += row
        return table
```

- [ ] **Step 3: Register the directive — update setup() and add _register_directives**

Directives must be registered after config is inited. In `coverage_report.py`, update `setup()` to add the builder-inited hook, and add the `_register_directives` function. After this step `setup()` should look like:

```python
def setup(app: Sphinx):
    # ... all app.add_config_value() calls from Task 5 ...
    app.connect("config-inited", _sphinx_needs_update)
    app.connect("builder-inited", install_styles_static_files)
    app.connect("builder-inited", _register_directives)   # ← add this line
    return {"version": VERSION, "parallel_read_safe": True, "parallel_write_safe": True}


def _register_directives(app):
    from sphinxcontrib.coverage_report.directives.coverage_results import CoverageResultsDirective
    app.add_directive("coverage-results", CoverageResultsDirective)
    # coverage-module, coverage-package, coverage-function, coverage-report added in Tasks 9 & 10
```

- [ ] **Step 4: Create Sphinx test project**

```python
# tests/doc_test/basic_results/conf.py
import sys, os
sys.path.insert(0, os.path.abspath("../../.."))
extensions = ["sphinxcontrib.coverage_report"]
```

```rst
.. tests/doc_test/basic_results/index.rst
Coverage Results
================

.. coverage-results:: ../../fixtures/coverage.xml
```

- [ ] **Step 5: Write test**

```python
# tests/test_coverage_results.py
import pytest
from sphinx.application import Sphinx
import os

@pytest.fixture
def build_app(tmp_path):
    src = os.path.join(os.path.dirname(__file__), "doc_test", "basic_results")
    out = str(tmp_path / "output")
    app = Sphinx(src, src, out, out, "html")
    app.build()
    return tmp_path

def test_build_succeeds(build_app):
    index_html = (build_app / "output" / "index.html").read_text()
    assert "module.py" in index_html
    assert "mypackage/module.py" in index_html

def test_line_rate_shown(build_app):
    html = (build_app / "output" / "index.html").read_text()
    assert "92%" in html or "80%" in html  # at least one module rate
```

- [ ] **Step 6: Run test**

```bash
pytest tests/test_coverage_results.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add sphinxcontrib/coverage_report/directives/ tests/doc_test/basic_results/ tests/test_coverage_results.py
git commit -m "feat: coverage-results standalone table directive"
```

---

## Task 7: Threshold-based status

**Files:**
- Modify: `sphinxcontrib/coverage_report/config.py` (already has `compute_status`)
- Create: `tests/test_threshold_status.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_threshold_status.py
from types import SimpleNamespace
from sphinxcontrib.coverage_report.config import compute_status

def make_config(**overrides):
    defaults = dict(
        cr_threshold_line_rate=0.80,
        cr_threshold_branch_rate=0.75,
        cr_threshold_report={},
        cr_threshold_package={},
        cr_threshold_module={},
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)

def test_passing_above_threshold():
    cfg = make_config()
    assert compute_status({"line_rate": 0.90, "branch_rate": 0.80, "branches_valid": 10}, cfg) == "passing"

def test_failing_below_line_threshold():
    cfg = make_config()
    assert compute_status({"line_rate": 0.70, "branch_rate": 0.80, "branches_valid": 10}, cfg) == "failing"

def test_failing_below_branch_threshold():
    cfg = make_config()
    assert compute_status({"line_rate": 0.90, "branch_rate": 0.50, "branches_valid": 10}, cfg) == "failing"

def test_no_branches_ignores_branch_threshold():
    cfg = make_config()
    assert compute_status({"line_rate": 0.90, "branch_rate": 0.0, "branches_valid": 0}, cfg) == "passing"

def test_per_level_override_wins():
    cfg = make_config(cr_threshold_module={"line_rate": 0.95})
    # 0.90 is above global 0.80 but below module override 0.95
    assert compute_status({"line_rate": 0.90, "branch_rate": 0.80, "branches_valid": 0}, cfg, level="module") == "failing"
```

- [ ] **Step 2: Run to confirm they pass (config.py was already written)**

```bash
pytest tests/test_threshold_status.py -v
```
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_threshold_status.py
git commit -m "test: threshold status unit tests"
```

---

## Task 8: Missing data warnings

**Files:**
- Create: `tests/fixtures/coverage_empty.xml`
- Create: `tests/test_warnings.py`

- [ ] **Step 1: Create empty fixture**

```xml
<!-- tests/fixtures/coverage_empty.xml -->
<?xml version="1.0" ?>
<coverage version="7.4.0" timestamp="1711180800" lines-valid="0"
          lines-covered="0" line-rate="0" branches-covered="0"
          branches-valid="0" branch-rate="0" complexity="0">
    <packages/>
</coverage>
```

- [ ] **Step 2: Write tests**

```python
# tests/test_warnings.py
import os
import pytest
from unittest.mock import patch, MagicMock
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective, _load_coverage_file,
)

def make_app(warn_no_data=True, rootdir="/tmp"):
    app = MagicMock()
    app.config.cr_warn_no_data = warn_no_data
    app.config.cr_rootdir = rootdir
    app.coveragereport_data = {}
    return app

def make_directive(app):
    d = CoverageCommonDirective.__new__(CoverageCommonDirective)
    d.app = app
    d.env = MagicMock()
    d.env.docname = "index"
    d.lineno = 1
    return d

def test_warns_file_not_found(fixture_dir):
    app = make_app()
    d = make_directive(app)
    with patch("sphinxcontrib.coverage_report.directives.coverage_common.logger") as mock_log:
        d._warn_if_no_data("/nonexistent/coverage.xml", None)
        mock_log.warning.assert_called_once()
        assert "not found" in mock_log.warning.call_args[0][0]

def test_warns_empty_data(fixture_dir):
    app = make_app()
    d = make_directive(app)
    filepath = os.path.join(fixture_dir, "coverage_empty.xml")
    data = _load_coverage_file(filepath, app)
    with patch("sphinxcontrib.coverage_report.directives.coverage_common.logger") as mock_log:
        d._warn_if_no_data(filepath, data)
        mock_log.warning.assert_called_once()
        assert "no coverage data" in mock_log.warning.call_args[0][0]

def test_no_warn_when_disabled(fixture_dir):
    app = make_app(warn_no_data=False)
    d = make_directive(app)
    with patch("sphinxcontrib.coverage_report.directives.coverage_common.logger") as mock_log:
        d._warn_if_no_data("/nonexistent/coverage.xml", None)
        mock_log.warning.assert_not_called()

def test_warns_missing_identifier(fixture_dir):
    app = make_app()
    d = make_directive(app)
    filepath = os.path.join(fixture_dir, "coverage.xml")
    data = _load_coverage_file(filepath, app)
    with patch("sphinxcontrib.coverage_report.directives.coverage_common.logger") as mock_log:
        d._warn_if_no_data(filepath, data, identifier="nonexistent_module")
        mock_log.warning.assert_called_once()
        assert "nonexistent_module" in mock_log.warning.call_args[0][1]
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_warnings.py -v
```
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/coverage_empty.xml tests/test_warnings.py
git commit -m "test: missing data warning behaviour"
```

---

## Task 9: sphinx-needs directives (module, package, function)

These directives create need nodes. They follow the same pattern as `TestCaseDirective` in sphinx-test-reports.

**Files:**
- Create: `sphinxcontrib/coverage_report/directives/coverage_module.py`
- Create: `sphinxcontrib/coverage_report/directives/coverage_package.py`
- Create: `sphinxcontrib/coverage_report/directives/coverage_function.py`
- Create: `tests/doc_test/module_needs/conf.py`
- Create: `tests/doc_test/module_needs/index.rst`
- Create: `tests/test_coverage_module.py`

- [ ] **Step 1: Check how add_need and _make_hashed_id are imported in sphinx-test-reports**

```bash
grep -n "add_need\|make_hashed_id\|_make_hashed_id\|add_doc\|NeedsSphinxConfig" \
  /home/chris/develop/repos/open_source/sphinx-test-reports/sphinxcontrib/test_reports/directives/test_common.py | head -20
```

`_make_hashed_id` moved to `sphinx_needs.api.need` in sphinx-needs >= 4.0. Its signature is:
`_make_hashed_id(type_prefix: str, full_title: str, content: str, config: NeedsSphinxConfig) -> str`

The `id_length` comes from `NeedsSphinxConfig`, NOT from a positional arg. Import pattern:

```python
from importlib.metadata import version as _pkg_version
from sphinx_needs.config import NeedsSphinxConfig

_sn_major = int(_pkg_version("sphinx-needs").split(".")[0])
if _sn_major >= 4:
    from sphinx_needs.api.need import _make_hashed_id
else:
    from sphinx_needs.api import make_hashed_id as _make_hashed_id
```

`add_doc` must be called after `add_need` to register the document for incremental rebuild detection:

```python
from sphinx_needs.utils import add_doc
# after add_need():
add_doc(self.env, self.env.docname)
```

- [ ] **Step 2: Implement coverage_module.py**

```python
# sphinxcontrib/coverage_report/directives/coverage_module.py
from docutils.parsers.rst import directives
from sphinx_needs.api import add_need
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.utils import add_doc
from sphinxcontrib.coverage_report.config import compute_status
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective, _load_coverage_file,
)
from importlib.metadata import version as _pkg_version

_sn_major = int(_pkg_version("sphinx-needs").split(".")[0])
if _sn_major >= 4:
    from sphinx_needs.api.need import _make_hashed_id
else:
    from sphinx_needs.api import make_hashed_id as _make_hashed_id


class CoverageModuleDirective(CoverageCommonDirective):
    """
    Creates a sphinx-needs node for a single source file.

    Usage::

        .. coverage-module:: path/to/coverage.xml
           :package: mypackage
           :module: module.py
           :id: CM_001
    """
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "status": directives.unchanged,
        "tags": directives.unchanged,
        "links": directives.unchanged,
        "package": directives.unchanged,
        "module": directives.unchanged,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.app)
        pkg_name = self.options.get("package", "")
        mod_name = self.options.get("module", "")

        mod_data = self._find_module(data, pkg_name, mod_name)
        if mod_data is None:
            identifier = f"{pkg_name}/{mod_name}" if pkg_name else mod_name
            self._warn_if_no_data(filepath, data, identifier=identifier or None)
            return []

        cfg = self.app.config
        need_type = cfg.cr_module[1]
        sn_cfg = NeedsSphinxConfig(cfg)
        need_id = self.options.get("id") or _make_hashed_id(
            need_type, f"{filepath}{pkg_name}{mod_name}", "", sn_cfg
        )

        status = self.options.get("status") or compute_status(mod_data, cfg, "module")
        title = f"{cfg.cr_module[2]}: {mod_data['filename']}"
        options = dict(
            line_rate=str(mod_data["line_rate"]),
            branch_rate=str(mod_data["branch_rate"]),
            lines_valid=str(mod_data["lines_valid"]),
            lines_covered=str(mod_data["lines_covered"]),
            branches_valid=str(mod_data["branches_valid"]),
            branches_covered=str(mod_data["branches_covered"]),
            missed_lines=", ".join(str(l) for l in mod_data["missed_lines"]),
            filename=mod_data["filename"],
            package=pkg_name,
            complexity=str(mod_data["complexity"]),
        )
        result = add_need(
            self.app, self.state, self.env.docname, self.lineno,
            need_type=need_type,
            title=title,
            id=need_id,
            status=status,
            tags=self.options.get("tags", ""),
            links=self.options.get("links", ""),
            **options,
        )
        add_doc(self.env, self.env.docname)
        return result

    @staticmethod
    def _find_module(data, pkg_name, mod_name):
        if data is None:
            return None
        for pkg in data.get("packages", []):
            if pkg_name and pkg["name"] != pkg_name:
                continue
            for mod in pkg.get("modules", []):
                if not mod_name or mod["name"] == mod_name or mod["filename"] == mod_name:
                    return mod
        return None
```

- [ ] **Step 3: Implement coverage_package.py (same pattern)**

```python
# sphinxcontrib/coverage_report/directives/coverage_package.py
from docutils.parsers.rst import directives
from sphinx_needs.api import add_need
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.utils import add_doc
from sphinxcontrib.coverage_report.config import compute_status
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective, _load_coverage_file,
)
from importlib.metadata import version as _pkg_version

_sn_major = int(_pkg_version("sphinx-needs").split(".")[0])
if _sn_major >= 4:
    from sphinx_needs.api.need import _make_hashed_id
else:
    from sphinx_needs.api import make_hashed_id as _make_hashed_id


class CoveragePackageDirective(CoverageCommonDirective):
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "status": directives.unchanged,
        "tags": directives.unchanged,
        "links": directives.unchanged,
        "package": directives.unchanged,
        "expand": directives.flag,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.app)
        pkg_name = self.options.get("package", "")
        pkg_data = self._find_package(data, pkg_name)

        if pkg_data is None:
            self._warn_if_no_data(filepath, data, identifier=pkg_name or None)
            return []

        cfg = self.app.config
        need_type = cfg.cr_package[1]
        sn_cfg = NeedsSphinxConfig(cfg)
        need_id = self.options.get("id") or _make_hashed_id(
            need_type, f"{filepath}{pkg_name}", "", sn_cfg
        )
        status = self.options.get("status") or compute_status(pkg_data, cfg, "package")
        title = f"{cfg.cr_package[2]}: {pkg_data['name']}"
        options = dict(
            line_rate=str(pkg_data["line_rate"]),
            branch_rate=str(pkg_data["branch_rate"]),
            lines_valid=str(pkg_data["lines_valid"]),
            lines_covered=str(pkg_data["lines_covered"]),
            branches_valid=str(pkg_data["branches_valid"]),
            branches_covered=str(pkg_data["branches_covered"]),
            package=pkg_data["name"],
        )
        result_nodes = add_need(
            self.app, self.state, self.env.docname, self.lineno,
            need_type=need_type,
            title=title,
            id=need_id,
            status=status,
            tags=self.options.get("tags", ""),
            links=self.options.get("links", ""),
            **options,
        )
        add_doc(self.env, self.env.docname)

        if "expand" in self.options:
            from sphinxcontrib.coverage_report.directives.coverage_module import CoverageModuleDirective
            for mod in pkg_data["modules"]:
                child_opts = {
                    "package": pkg_data["name"],
                    "module": mod["name"],
                    "links": need_id,
                }
                child = CoverageModuleDirective(
                    self.name, [self.arguments[0]], child_opts,
                    self.content, self.lineno, self.content_offset,
                    self.block_text, self.state, self.state_machine,
                )
                result_nodes.extend(child.run())

        return result_nodes

    @staticmethod
    def _find_package(data, pkg_name):
        if data is None:
            return None
        for pkg in data.get("packages", []):
            if not pkg_name or pkg["name"] == pkg_name:
                return pkg
        return None
```

- [ ] **Step 4: Implement coverage_function.py**

```python
# sphinxcontrib/coverage_report/directives/coverage_function.py
from docutils.parsers.rst import directives
from sphinx_needs.api import add_need
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.utils import add_doc
from sphinxcontrib.coverage_report.config import compute_status
from sphinxcontrib.coverage_report.directives.coverage_common import (
    CoverageCommonDirective, _load_coverage_file,
)
from importlib.metadata import version as _pkg_version

_sn_major = int(_pkg_version("sphinx-needs").split(".")[0])
if _sn_major >= 4:
    from sphinx_needs.api.need import _make_hashed_id
else:
    from sphinx_needs.api import make_hashed_id as _make_hashed_id


class CoverageFunctionDirective(CoverageCommonDirective):
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "status": directives.unchanged,
        "tags": directives.unchanged,
        "links": directives.unchanged,
        "package": directives.unchanged,
        "module": directives.unchanged,
        "function": directives.unchanged,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        data = _load_coverage_file(filepath, self.app)
        pkg_name = self.options.get("package", "")
        mod_name = self.options.get("module", "")
        fn_name = self.options.get("function", "")

        fn_data = self._find_function(data, pkg_name, mod_name, fn_name)
        if fn_data is None:
            self._warn_if_no_data(filepath, data, identifier=fn_name or None)
            return []

        cfg = self.app.config
        need_type = cfg.cr_function[1]
        sn_cfg = NeedsSphinxConfig(cfg)
        need_id = self.options.get("id") or _make_hashed_id(
            need_type, f"{filepath}{pkg_name}{mod_name}{fn_name}", "", sn_cfg
        )
        # Functions have no branch data; pass branches_valid=0 to skip branch threshold
        fn_data_with_bv = {**fn_data, "branches_valid": 0}
        status = self.options.get("status") or compute_status(fn_data_with_bv, cfg, "module")
        title = f"{cfg.cr_function[2]}: {fn_data['name']}"
        result = add_need(
            self.app, self.state, self.env.docname, self.lineno,
            need_type=need_type,
            title=title,
            id=need_id,
            status=status,
            tags=self.options.get("tags", ""),
            links=self.options.get("links", ""),
            hits=str(fn_data["hits"]),
            line_start=str(fn_data["line_start"]),
            filename=mod_name,
            package=pkg_name,
        )
        add_doc(self.env, self.env.docname)
        return result

    @staticmethod
    def _find_function(data, pkg_name, mod_name, fn_name):
        if data is None:
            return None
        for pkg in data.get("packages", []):
            if pkg_name and pkg["name"] != pkg_name:
                continue
            for mod in pkg.get("modules", []):
                if mod_name and mod["name"] != mod_name and mod["filename"] != mod_name:
                    continue
                for fn in mod.get("functions", []):
                    if not fn_name or fn["name"] == fn_name:
                        return fn
        return None
```

- [ ] **Step 5: Register new directives in coverage_report.py**

Update `_register_directives()`:

```python
def _register_directives(app):
    from sphinxcontrib.coverage_report.directives.coverage_results import CoverageResultsDirective
    from sphinxcontrib.coverage_report.directives.coverage_module import CoverageModuleDirective
    from sphinxcontrib.coverage_report.directives.coverage_package import CoveragePackageDirective
    from sphinxcontrib.coverage_report.directives.coverage_function import CoverageFunctionDirective
    app.add_directive("coverage-results", CoverageResultsDirective)
    app.add_directive(app.config.cr_module[0], CoverageModuleDirective)
    app.add_directive(app.config.cr_package[0], CoveragePackageDirective)
    app.add_directive(app.config.cr_function[0], CoverageFunctionDirective)
```

- [ ] **Step 6: Create Sphinx test project**

```python
# tests/doc_test/module_needs/conf.py
import sys, os
sys.path.insert(0, os.path.abspath("../../.."))
extensions = ["sphinx_needs", "sphinxcontrib.coverage_report"]
needs_id_regex = ".*"
```

```rst
.. tests/doc_test/module_needs/index.rst
Module Coverage
===============

.. coverage-module:: ../../fixtures/coverage.xml
   :package: mypackage
   :module: module.py
```

- [ ] **Step 7: Write and run integration test**

```python
# tests/test_coverage_module.py
import os
import pytest
from sphinx.application import Sphinx

@pytest.fixture
def build_app(tmp_path):
    src = os.path.join(os.path.dirname(__file__), "doc_test", "module_needs")
    out = str(tmp_path / "output")
    app = Sphinx(src, src, out, out, "html")
    app.build()
    return tmp_path

def test_build_succeeds(build_app):
    html = (build_app / "output" / "index.html").read_text()
    assert "mypackage/module.py" in html

def test_coverage_module_need_rendered(build_app):
    html = (build_app / "output" / "index.html").read_text()
    # Need node title should appear
    assert "Coverage Module" in html
```

```bash
pytest tests/test_coverage_module.py -v
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add sphinxcontrib/coverage_report/directives/ tests/doc_test/module_needs/ tests/test_coverage_module.py
git commit -m "feat: coverage-module, coverage-package, coverage-function need directives"
```

---

## Task 10: coverage-report template directive

**Files:**
- Create: `sphinxcontrib/coverage_report/directives/coverage_report_directive.py`
- Create: `sphinxcontrib/coverage_report/directives/coverage_report_template.txt`
- Create: `tests/doc_test/full_report/`

- [ ] **Step 1: Create default template**

```
{title}
{title_underline}

.. coverage-results:: {file}

.. needtable::
   :filter: type == '{module_need}' and '{id}' in tags
   :columns: id, title, status, line_rate, branch_rate
   :style: table
```

Where `{title}`, `{file}`, `{id}`, `{module_need}`, `{title_underline}` are substituted at directive run time.

- [ ] **Step 2: Implement coverage_report_directive.py**

```python
# sphinxcontrib/coverage_report/directives/coverage_report_directive.py
from docutils.parsers.rst import directives
from sphinxcontrib.coverage_report.directives.coverage_common import CoverageCommonDirective


class CoverageReportDirective(CoverageCommonDirective):
    """
    Template-based full coverage report.

    Reads the template file, substitutes variables, and inserts the
    expanded RST back into the document via state_machine.insert_input().
    """
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged,
        "tags": directives.unchanged,
        "title": directives.unchanged,
    }
    has_content = False

    def run(self):
        filepath = self._resolve_path(self.arguments[0])
        cfg = self.app.config
        template_path = cfg.cr_report_template

        with open(template_path, encoding="utf-8") as fh:
            template = fh.read()

        report_id = self.options.get("id", "CR_REPORT")
        title = self.options.get("title", f"Coverage Report: {filepath}")
        rst = template.format(
            file=self.arguments[0],
            id=report_id,
            tags=self.options.get("tags", report_id),
            title=title,
            title_underline="=" * len(title),
            module_need=cfg.cr_module[1],
            package_need=cfg.cr_package[1],
        )
        self.state_machine.insert_input(rst.splitlines(), self.arguments[0])
        return []
```

- [ ] **Step 3: Register in _register_directives()**

```python
from sphinxcontrib.coverage_report.directives.coverage_report_directive import CoverageReportDirective
app.add_directive(app.config.cr_report[0], CoverageReportDirective)
```

- [ ] **Step 4: Create Sphinx test project and test**

```python
# tests/doc_test/full_report/conf.py
import sys, os
sys.path.insert(0, os.path.abspath("../../.."))
extensions = ["sphinx_needs", "sphinxcontrib.coverage_report"]
needs_id_regex = ".*"
```

```rst
.. tests/doc_test/full_report/index.rst
Full Report
===========

.. coverage-report:: ../../fixtures/coverage.xml
   :id: CR_TEST
   :title: Test Coverage Report
```

```python
# add to tests/test_coverage_results.py or a new file:
def test_coverage_report_directive_builds(tmp_path):
    src = os.path.join(os.path.dirname(__file__), "doc_test", "full_report")
    out = str(tmp_path / "output")
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, out, "html")
    app.build()
    html = (tmp_path / "output" / "index.html").read_text()
    assert "Test Coverage Report" in html
```

```bash
pytest tests/test_coverage_results.py -v -k "report"
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sphinxcontrib/coverage_report/directives/coverage_report_directive.py \
        sphinxcontrib/coverage_report/directives/coverage_report_template.txt \
        tests/doc_test/full_report/
git commit -m "feat: coverage-report template directive"
```

---

## Task 11: cr_link() dynamic function

**Files:**
- Modify: `sphinxcontrib/coverage_report/functions/__init__.py`
- Create: `tests/test_cr_link.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cr_link.py
from sphinxcontrib.coverage_report.functions import cr_link

def make_need(**kwargs):
    return {"id": "TEST", "type": "coveragemodule", **kwargs}

def make_needs(*items):
    return {n["id"]: n for n in items}

def test_cr_link_matches_on_filename():
    coverage_need = make_need(type="coveragemodule", filename="mypackage/module.py")
    tc1 = make_need(id="TC_001", type="testcase", file="mypackage/module.py")
    tc2 = make_need(id="TC_002", type="testcase", file="mypackage/other.py")
    needs = make_needs(coverage_need, tc1, tc2)

    result = cr_link(None, coverage_need, needs, "filename", filter_string="file")
    assert "TC_001" in result
    assert "TC_002" not in result

def test_cr_link_no_match_returns_empty():
    coverage_need = make_need(type="coveragemodule", filename="mypackage/module.py")
    tc1 = make_need(id="TC_001", type="testcase", file="mypackage/other.py")
    needs = make_needs(coverage_need, tc1)
    result = cr_link(None, coverage_need, needs, "filename", filter_string="file")
    assert result == []

def test_cr_link_missing_option_returns_empty():
    coverage_need = make_need(type="coveragemodule")  # no filename
    needs = make_needs(coverage_need)
    result = cr_link(None, coverage_need, needs, "filename", filter_string="file")
    assert result == []
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_cr_link.py -v
```
Expected: FAIL (stub returns `[]` for all)

- [ ] **Step 3: Implement cr_link()**

```python
# sphinxcontrib/coverage_report/functions/__init__.py
def cr_link(app, need, needs, option, filter_string=None, **kwargs):
    """
    Dynamic function for sphinx-needs.

    Returns IDs of needs whose `filter_string` option value matches
    the current need's `option` value.

    Example RST usage::

        :links: [[cr_link('filename', 'file')]]

    This links a coverage-module node to all test-case nodes whose
    ':file:' option matches the coverage module's 'filename' option.
    """
    match_value = need.get(option)
    if not match_value:
        return []
    target_field = filter_string or option
    return [
        n["id"]
        for n in needs.values()
        if n.get(target_field) == match_value and n["id"] != need["id"]
    ]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cr_link.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add sphinxcontrib/coverage_report/functions/__init__.py tests/test_cr_link.py
git commit -m "feat: cr_link() dynamic function for cross-linking to test-case nodes"
```

---

## Task 12: nox + CI setup

**Files:**
- Create: `noxfile.py`
- Create: `.github/workflows/ci.yaml`

- [ ] **Step 1: Create noxfile.py**

```python
# noxfile.py
import nox

PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]
SPHINX_NEEDS_VERSIONS = ["6.3.0", "7.0.0", "8.0.0"]


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("sphinx_needs", SPHINX_NEEDS_VERSIONS)
def tests(session, sphinx_needs):
    session.install("-e", ".[test]")
    session.install(f"sphinx-needs=={sphinx_needs}")
    session.run("pytest", "tests/", "-v", "--tb=short")


@nox.session
def lint(session):
    session.install("ruff")
    session.run("ruff", "check", "sphinxcontrib/", "tests/")


@nox.session
def coverage(session):
    session.install("-e", ".[test]")
    session.run(
        "pytest", "tests/", "--cov=sphinxcontrib/coverage_report",
        "--cov-report=xml", "--cov-report=term-missing",
    )
```

- [ ] **Step 2: Create .github/workflows/ci.yaml**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
        sphinx-needs: ["6.3.0", "7.0.0", "8.0.0"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install nox
      - run: nox -s "tests-${{ matrix.python-version }}(sphinx_needs='${{ matrix.sphinx-needs }}')"

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install nox && nox -s lint
```

- [ ] **Step 3: Run full test suite locally**

```bash
pytest tests/ -v
```
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add noxfile.py .github/
git commit -m "chore: nox matrix + GitHub Actions CI"
```

---

## Task 13: Final integration smoke test

- [ ] **Step 1: Run complete test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: all PASS, no warnings about missing fixtures

- [ ] **Step 2: Build docs with sphinx to verify extension loads cleanly**

```bash
cd tests/doc_test/module_needs && python -m sphinx . /tmp/cr_test_build -b html -W
```
Expected: build succeeds, no warnings as errors

- [ ] **Step 3: Verify package is installable**

```bash
pip install build && python -m build --wheel && pip install dist/*.whl
python -c "import sphinxcontrib.coverage_report; print('install ok')"
```
Expected: `install ok`

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "chore: final integration verification"
```
