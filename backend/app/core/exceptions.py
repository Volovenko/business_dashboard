from __future__ import annotations


class DomainError(Exception):
    """Base class for domain-level errors (mapped to HTTP responses at the API edge)."""


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity: str, entity_id: object) -> None:
        super().__init__(f"{entity} with id={entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(DomainError):
    """Raised when input is structurally valid but semantically invalid."""


class ImportError(DomainError):
    """Raised when bank statement import fails (parser/filter/mapper)."""
