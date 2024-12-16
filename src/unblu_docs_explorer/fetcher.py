"""Documentation fetcher module."""

from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .models.document import Document, DocumentSection
from .errors import DocumentationError, ResourceNotFoundError


class DocumentationFetcher:
    """Fetches and processes documentation content."""

    def __init__(self, base_url: str, http_client: httpx.AsyncClient | None = None):
        """Initialize the fetcher with a base URL and optional HTTP client."""
        self.base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.AsyncClient()
        self._cache = {}

    async def __aenter__(self):
        """Enter the async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        await self._http_client.aclose()

    def _build_url(self, path: str) -> str:
        """Build a full URL from a path."""
        # Remove leading and trailing slashes from path
        path = path.strip("/")
        # Ensure there's no double slash between base_url and path
        return f"{self.base_url}/{path}"

    async def fetch_document(self, path: str) -> Document:
        """Fetch and process a document from the given path."""
        url = self._build_url(path)

        # Check cache first
        if url in self._cache:
            return self._cache[url]

        try:
            response = await self._http_client.get(url)

            if response.status_code == 404:
                raise ResourceNotFoundError(message="Document not found", operation="fetch_document")
            elif response.status_code >= 500:
                raise DocumentationError(
                    message=f"Server error {response.status_code} while fetching document", operation="fetch_document"
                )

            response.raise_for_status()

        except httpx.RequestError as e:
            raise DocumentationError(message=f"Failed to fetch document: {e}", operation="fetch_document") from e

        soup = BeautifulSoup(response.text, "html.parser")
        try:
            title = soup.title.string.strip() if soup.title and soup.title.string else path
        except (AttributeError, ValueError):
            title = path

        sections = []

        # Process sections (h1 headers)
        for h1 in soup.find_all("h1"):
            section_content = []
            current = h1.next_sibling

            while current and current.name != "h1":
                if isinstance(current, str):
                    if current.strip():
                        section_content.append(current.strip())
                else:
                    section_content.append(current.get_text().strip())
                current = current.next_sibling

            sections.append(
                DocumentSection(title=h1.get_text().strip(), content=" ".join(filter(None, section_content)))
            )

        doc = Document(url=url, title=title, sections=sections, last_fetched=datetime.now(timezone.utc))
        self._cache[url] = doc
        return doc

    async def invalidate_cache(self, path: str | None = None):
        """Invalidate the cache for a specific path or all paths."""
        if path is None:
            self._cache.clear()
        else:
            url = self._build_url(path)
            if url in self._cache:
                del self._cache[url]
