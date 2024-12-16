from typing import Dict, List, Optional
from dataclasses import dataclass, field
from .errors import SearchError


@dataclass
class Document:
    """Represents a documentation document with its metadata."""

    title: str
    content: str
    path: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """Represents a search result with relevance score."""

    path: str
    title: str
    content: str
    relevance: float
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "relevance": self.relevance,
            "metadata": self.metadata,
        }


class DocumentationSearch:
    """Simple search implementation for documentation."""

    def __init__(self):
        self._documents: List[Document] = []

    async def index_document(self, doc_data: Dict) -> None:
        """Index a document for searching."""
        document = Document(
            title=doc_data["title"],
            content=doc_data["content"],
            path=doc_data["path"],
            metadata=doc_data.get("metadata", {}),
        )
        self._documents.append(document)

    def _calculate_relevance(self, doc: Document, query: str, context: Optional[str] = None) -> float:
        """Calculate relevance score for a document."""
        if context and doc.metadata.get("section") != context:
            return 0.0

        query = query.lower()
        title_matches = sum(term in doc.title.lower() for term in query.split())
        content_matches = sum(term in doc.content.lower() for term in query.split())

        # Title matches are weighted more heavily
        return (title_matches * 2.0 + content_matches) / (len(query.split()) * 3.0)

    async def search(self, query: str, context: Optional[str] = None) -> List[Dict]:
        """
        Search for documents matching the query.

        Args:
            query: Search query string
            context: Optional context to filter results (e.g., "api", "user")

        Returns:
            List of matching documents with relevance scores

        Raises:
            SearchError: If query is empty
        """
        if not query.strip():
            raise SearchError("Search query cannot be empty")

        results = []
        for doc in self._documents:
            relevance = self._calculate_relevance(doc, query, context)
            if relevance > 0:
                results.append(
                    SearchResult(
                        path=doc.path, title=doc.title, content=doc.content, relevance=relevance, metadata=doc.metadata
                    ).to_dict()
                )

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results
