"""Test configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_doc_html():
    """Provide sample HTML content for testing."""
    return """
    <html>
        <head><title>Test Doc</title></head>
        <body>
            <h1>Test Section</h1>
            <p>Test content</p>
        </body>
    </html>
    """
