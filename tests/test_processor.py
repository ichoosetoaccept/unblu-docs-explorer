"""Tests for the documentation processor."""

import pytest

from unblu_docs_explorer.processor import DocumentProcessor
from unblu_docs_explorer.models.document import Document

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_processed_html():
    """Sample HTML document for testing processing."""
    return """
    <html>
        <head><title>Test Documentation</title></head>
        <body>
            <h1>Main Concept</h1>
            <p>This is an introduction to the main concept.</p>
            <h2>Implementation Details</h2>
            <p>Here are the implementation details:</p>
            <ul>
                <li>First point</li>
                <li>Second point</li>
            </ul>
            <h2>Configuration</h2>
            <pre><code>
            {
                "setting": "value"
            }
            </code></pre>
            <h1>Advanced Usage</h1>
            <p>Advanced usage information.</p>
        </body>
    </html>
    """


@pytest.fixture
def processor():
    """Create a DocumentProcessor instance for testing."""
    return DocumentProcessor()


async def test_process_document_structure(processor, sample_processed_html):
    """Test that document structure is correctly processed."""
    doc = await processor.process(sample_processed_html)

    assert isinstance(doc, Document)
    assert len(doc.sections) == 2

    main_section = doc.sections[0]
    assert main_section.title == "Main Concept"
    assert len(main_section.subsections) == 2
    assert "introduction to the main concept" in main_section.content.lower()


async def test_process_code_blocks(processor, sample_processed_html):
    """Test that code blocks are properly preserved and formatted."""
    doc = await processor.process(sample_processed_html)

    config_section = doc.sections[0].subsections[1]
    assert config_section.title == "Configuration"
    assert '"setting": "value"' in config_section.content


async def test_process_lists(processor, sample_processed_html):
    """Test that lists are properly processed."""
    doc = await processor.process(sample_processed_html)

    details_section = doc.sections[0].subsections[0]
    assert details_section.title == "Implementation Details"
    assert "First point" in details_section.content
    assert "Second point" in details_section.content


async def test_process_empty_document():
    """Test processing of an empty document."""
    processor = DocumentProcessor()

    with pytest.raises(ValueError, match="Empty document"):
        await processor.process("")


async def test_process_malformed_document():
    """Test processing of malformed HTML."""
    processor = DocumentProcessor()
    malformed_html = "<h1>Incomplete Document"

    with pytest.raises(ValueError, match="Malformed HTML"):
        await processor.process(malformed_html)


async def test_section_metadata(processor, sample_processed_html):
    """Test that section metadata is correctly extracted."""
    doc = await processor.process(sample_processed_html)

    for section in doc.sections:
        assert hasattr(section, "word_count")
        assert hasattr(section, "heading_level")
        assert section.heading_level >= 1
