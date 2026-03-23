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
