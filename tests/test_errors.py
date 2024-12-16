"""Tests for the error handling system."""

import pytest
from unblu_docs_explorer.errors import ErrorContext, DocumentationError, ResourceNotFoundError


@pytest.mark.asyncio
async def test_error_context_handles_exceptions():
    """Verify error context properly transforms exceptions."""
    with pytest.raises(DocumentationError) as exc_info:
        async with ErrorContext("test_operation").handle():
            raise ValueError("Test error")

    assert exc_info.value.operation == "test_operation"
    assert isinstance(exc_info.value.original_error, ValueError)
    assert "Test error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_error_context_preserves_stack_trace():
    """Ensure error transformation maintains debugging information."""
    with pytest.raises(DocumentationError) as exc_info:
        async with ErrorContext("nested_operation").handle():
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e

    assert exc_info.value.operation == "nested_operation"
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert isinstance(exc_info.value.__cause__.__cause__, ValueError)


@pytest.mark.asyncio
async def test_error_context_with_custom_error():
    """Verify error context can use custom error types."""
    with pytest.raises(ResourceNotFoundError) as exc_info:
        async with ErrorContext("find_resource").handle(ResourceNotFoundError):
            raise KeyError("Resource not found")

    assert isinstance(exc_info.value, ResourceNotFoundError)
    assert exc_info.value.operation == "find_resource"
