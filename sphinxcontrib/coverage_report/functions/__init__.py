# sphinxcontrib/coverage_report/functions/__init__.py
"""Dynamic functions for sphinx-needs integration."""


def cr_link(app, need, needs, option, filter_string=None, **kwargs):
    """Dynamic function for sphinx-needs.

    Returns IDs of needs whose ``filter_string`` option value matches
    the current need's ``option`` value.

    Example RST usage::

        :links: [[cr_link('filename', 'file')]]

    This links a coverage-module node to all test-case nodes whose
    ``:file:`` option matches the coverage module's ``filename`` option.
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
