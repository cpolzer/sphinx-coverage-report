import os
import pytest
from sphinxcontrib.coverage_report.jsonparser import JsonParser
from sphinxcontrib.coverage_report.exceptions import CoverageReportFileNotFound, CoverageReportFileInvalid

@pytest.fixture
def parser(fixture_dir):
    return JsonParser(os.path.join(fixture_dir, "coverage.json"))

def test_file_not_found_raises():
    with pytest.raises(CoverageReportFileNotFound):
        JsonParser("/nonexistent/coverage.json")

def test_malformed_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")
    with pytest.raises(CoverageReportFileInvalid):
        JsonParser(str(bad))

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

def test_parse_utils_no_functions(parser):
    mods = parser.parse()["packages"][0]["modules"]
    utils = next(m for m in mods if m["name"] == "utils.py")
    assert utils["functions"] == []
    assert utils["lines_valid"] == 2
