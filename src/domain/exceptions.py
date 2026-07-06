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


class SubstitutionNotFoundError(DomainError):
    """Raised when a substitution cannot be located by the repository."""

    def __init__(self, substitution_id: str) -> None:
        super().__init__(f"Substitution with id '{substitution_id}' was not found.")
        self.substitution_id = substitution_id


class UserNotFoundError(DomainError):
    """Raised when a user cannot be located by the repository."""

    def __init__(self, user_id: str) -> None:
        super().__init__(f"User with id '{user_id}' was not found.")
        self.user_id = user_id


class InventoryItemNotFoundError(DomainError):
    """Raised when an inventory item cannot be located by the repository."""

    def __init__(self, item_id: str) -> None:
        super().__init__(f"Inventory item with id '{item_id}' was not found.")
        self.item_id = item_id
