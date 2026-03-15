from typing import Protocol

from vigil.business_logic.models.report import Report


class ReportWriter(Protocol):
    """Interface for persisting an analysis report."""

    def write(self, report: Report) -> None:
        """Persist the report. Overwrites any previous report for the same video_id."""
        ...
