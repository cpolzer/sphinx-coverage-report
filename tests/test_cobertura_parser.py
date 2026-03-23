import os
import pytest
from sphinxcontrib.coverage_report.coberturaparser import CoberturaParser
from sphinxcontrib.coverage_report.exceptions import (
    CoverageReportFileNotFound,
    CoverageReportFileInvalid,
)


@pytest.fixture
def parser(fixture_dir):
    return CoberturaParser(os.path.join(fixture_dir, "coverage.xml"))


def test_file_not_found_raises():
    with pytest.raises(CoverageReportFileNotFound):
        CoberturaParser("/nonexistent/coverage.xml")


def test_malformed_xml_raises(fixture_dir, tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("not xml at all")
    with pytest.raises(CoverageReportFileInvalid):
        CoberturaParser(str(bad))


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
    # Numeric rollup fields derived from classes
    assert pkg["lines_valid"] == 7    # 5 lines in module.py + 2 in utils.py
    assert pkg["lines_covered"] == 4  # 3 hits in module.py + 1 in utils.py
    assert pkg["branches_valid"] == 2
    assert pkg["branches_covered"] == 1


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
