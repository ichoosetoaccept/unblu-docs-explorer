"""Error handling system for the Unblu Documentation Explorer."""

from contextlib import asynccontextmanager
from typing import Optional, Type


class DocumentationError(Exception):
    """Base exception class for documentation-related errors."""

    def __init__(self, message: str, operation: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.operation = operation
        self.original_error = original_error


class ResourceNotFoundError(DocumentationError):
    """Raised when a requested resource cannot be found."""

    pass


class SearchError(DocumentationError):
    """Raised when there is an error during search operations."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, operation="search", original_error=original_error)


class ErrorContext:
    """Context manager for handling and transforming exceptions."""

    def __init__(self, operation: str):
        self.operation = operation

    @asynccontextmanager
    async def handle(self, error_type: Type[DocumentationError] = DocumentationError):
        """Handle exceptions and transform them into DocumentationError types."""
        try:
            yield
        except DocumentationError:
            # Already a DocumentationError, re-raise as is
            raise
        except Exception as e:
            message = f"Error during {self.operation}: {str(e)}"
            raise error_type(message, self.operation, e) from e
