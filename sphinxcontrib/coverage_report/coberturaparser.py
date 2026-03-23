"""Parser for Cobertura XML coverage reports."""

import os
from lxml import etree
from sphinxcontrib.coverage_report.exceptions import (
    CoverageReportFileNotFound,
    CoverageReportFileInvalid,
)


class CoberturaParser:
    """Parse a Cobertura-format XML coverage report into a plain dict structure."""

    def __init__(self, xml_path, xsd_path=None):
        """Initialise the parser and load the XML document.

        Args:
            xml_path: Path to the Cobertura XML file.
            xsd_path: Optional path to an XSD schema for validation.  When
                omitted the bundled ``cobertura.xsd`` is used.

        Raises:
            CoverageReportFileNotFound: If *xml_path* does not exist.
            CoverageReportFileInvalid: If *xml_path* cannot be parsed as XML.
        """
        if not os.path.exists(xml_path):
            raise CoverageReportFileNotFound(f"File not found: {xml_path}")
        self.xml_path = xml_path
        self.xsd_path = xsd_path or os.path.join(
            os.path.dirname(__file__), "schemas", "cobertura.xsd"
        )
        try:
            self._doc = etree.parse(xml_path)
        except etree.XMLSyntaxError as exc:
            raise CoverageReportFileInvalid(
                f"Cannot parse {xml_path}: {exc}"
            ) from exc

    def validate(self):
        """Validate the document against the Cobertura XSD schema.

        Returns ``True`` when the schema file is absent (schema is optional).
        """
        if not os.path.exists(self.xsd_path):
            return True  # schema optional
        schema = etree.XMLSchema(etree.parse(self.xsd_path))
        return schema.validate(self._doc)

    def parse(self):
        """Parse the XML document and return a coverage report dict.

        Returns:
            A dict with top-level coverage metrics and a ``packages`` list.
        """
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
        """Parse all ``<package>`` elements under *root*.

        Returns:
            A list of package dicts, each containing a ``modules`` list with
            per-class data and numeric rollup totals derived from those classes.
        """
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
        """Parse a single ``<class>`` element into a module dict.

        Returns:
            A dict with coverage metrics, missed line numbers, and an empty
            ``functions`` list (Cobertura does not carry function-level data).
        """
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
