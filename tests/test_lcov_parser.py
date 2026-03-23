import os
import pytest
from sphinxcontrib.coverage_report.lcovparser import LcovParser
from sphinxcontrib.coverage_report.exceptions import (
    CoverageReportFileNotFound,
    CoverageReportFileInvalid,
)

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

def test_malformed_lcov_raises(tmp_path):
    bad = tmp_path / "bad.info"
    bad.write_text("FNDA:notanumber,myfunc\n")
    with pytest.raises(CoverageReportFileInvalid):
        LcovParser(str(bad)).parse()

def test_parse_second_module(parser):
    """utils.py has no functions and one missed line."""
    mods = parser.parse()["packages"][0]["modules"]
    utils = next(m for m in mods if m["name"] == "utils.py")
    assert utils["filename"] == "mypackage/utils.py"
    assert utils["functions"] == []
    assert utils["lines_valid"] == 2
    assert utils["lines_covered"] == 1
    assert 3 in utils["missed_lines"]

def test_parse_module_branch_fields(parser):
    mod = parser.parse()["packages"][0]["modules"][0]
    assert mod["branches_valid"] == 2
    assert mod["branches_covered"] == 1
    assert mod["branch_rate"] == pytest.approx(0.5)
