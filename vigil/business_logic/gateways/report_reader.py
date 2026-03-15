from typing import Protocol
from uuid import UUID

from vigil.business_logic.models.report import Report


class ReportReader(Protocol):
    """Interface for reading a previously persisted analysis report."""

    def read(self, video_id: UUID) -> Report | None:
        """Return the report for video_id, or None if not found."""
        ...
