class CoverageReportError(Exception):
    pass


class CoverageReportFileNotFound(CoverageReportError):
    pass


class CoverageReportFileInvalid(CoverageReportError):
    pass


class CoverageReportInvalidOption(CoverageReportError):
    pass
