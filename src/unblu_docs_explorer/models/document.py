"""Document model for representing Unblu documentation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class DocumentSection:
    """Represents a section within a document."""

    title: str
    content: str
    subsections: List["DocumentSection"] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a complete documentation document."""

    url: str
    title: str
    sections: List[DocumentSection]
    metadata: Dict[str, str] = field(default_factory=dict)
    last_fetched: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_section(self, section: DocumentSection) -> None:
        """Add a section to the document."""
        self.sections.append(section)

    def update_metadata(self, key: str, value: str) -> None:
        """Update document metadata."""
        self.metadata[key] = value

    def mark_fetched(self) -> None:
        """Mark document as fetched with current timestamp."""
        self.last_fetched = datetime.now(timezone.utc)
