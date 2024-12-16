"""Documentation processor for structuring and analyzing HTML content."""

from bs4 import BeautifulSoup
from typing import List, Optional

from .models.document import Document, DocumentSection


class DocumentProcessor:
    """Processes HTML documentation into structured Document objects."""

    def __init__(self):
        """Initialize the document processor."""
        self.current_section: Optional[DocumentSection] = None
        self.section_stack: List[DocumentSection] = []

    async def process(self, html_content: str) -> Document:
        """Process HTML content into a structured document.

        Args:
            html_content: Raw HTML content to process

        Returns:
            Document: Structured document with sections and metadata

        Raises:
            ValueError: If the document is empty or malformed
        """
        if not html_content.strip():
            raise ValueError("Empty document")

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            # Validate basic HTML structure
            if not soup.find("html") or not soup.find("body"):
                raise ValueError("Malformed HTML: Missing required html or body tags")
        except Exception as e:
            raise ValueError(f"Malformed HTML: {str(e)}")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.text if title_tag else "Untitled Document"

        # Create document
        doc = Document(url="", title=title, sections=[])

        # Process body content
        body = soup.find("body")
        if not body:
            return doc  # Return empty document if no body found

        current_section = None
        content_buffer = []

        for elem in body.children:
            if elem.name and elem.name.startswith("h") and len(elem.name) == 2:
                # Process any buffered content
                if current_section and content_buffer:
                    current_section.content = "\n".join(content_buffer)
                    content_buffer = []

                # Get heading level
                level = int(elem.name[1])

                # Create new section
                section = DocumentSection(title=elem.text.strip(), content="", heading_level=level)

                # Handle section hierarchy
                if level == 1:
                    doc.sections.append(section)
                    current_section = section
                elif current_section:
                    # Find appropriate parent section
                    parent = current_section
                    while parent and parent.heading_level >= level:
                        if len(doc.sections) > 0:
                            parent = doc.sections[-1]
                        else:
                            parent = None

                    if parent:
                        parent.subsections.append(section)
                    else:
                        # If no appropriate parent found, add as top-level section
                        doc.sections.append(section)
                    current_section = section

            elif current_section:
                # Process content elements
                if elem.name in ["p", "pre", "code", "ul", "ol"]:
                    content_buffer.append(elem.text.strip())

        # Process any remaining buffered content
        if current_section and content_buffer:
            current_section.content = "\n".join(content_buffer)

        # Calculate word counts
        for section in doc.sections:
            section.calculate_word_count()

        return doc
