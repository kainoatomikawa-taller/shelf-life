"""Domain-level exceptions.

These express violations of business rules. They are raised by entities,
value objects and domain services and are translated into transport-specific
responses by the interfaces layer.
"""


class DomainError(Exception):
    """Base class for all domain errors."""


class ValidationError(DomainError):
    """Raised when a domain invariant is violated."""


class PantryItemNotFoundError(DomainError):
    """Raised when a pantry item cannot be located by the repository."""

    def __init__(self, item_id: str) -> None:
        super().__init__(f"Pantry item with id '{item_id}' was not found.")
        self.item_id = item_id


class IngredientNotFoundError(DomainError):
    """Raised when an ingredient cannot be located by the repository."""

    def __init__(self, ingredient_id: str) -> None:
        super().__init__(f"Ingredient with id '{ingredient_id}' was not found.")
        self.ingredient_id = ingredient_id
