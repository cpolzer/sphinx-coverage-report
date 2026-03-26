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
