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


class RecipeNotFoundError(DomainError):
    """Raised when a recipe cannot be located by the repository."""

    def __init__(self, recipe_id: str) -> None:
        super().__init__(f"Recipe with id '{recipe_id}' was not found.")
        self.recipe_id = recipe_id


class ShoppingListItemNotFoundError(DomainError):
    """Raised when a shopping list item cannot be located by the repository."""

    def __init__(self, item_id: str) -> None:
        super().__init__(f"Shopping list item with id '{item_id}' was not found.")
        self.item_id = item_id


class RawRecipeNotFoundError(DomainError):
    """Raised when a staged raw recipe cannot be located by the repository."""

    def __init__(self, raw_recipe_id: str) -> None:
        super().__init__(f"Raw recipe with id '{raw_recipe_id}' was not found.")
        self.raw_recipe_id = raw_recipe_id


class DuplicateRawRecipeError(DomainError):
    """Raised when a raw recipe is imported twice from the same source."""

    def __init__(self, source: str, source_recipe_id: str) -> None:
        super().__init__(
            f"A raw recipe from source '{source}' with source_recipe_id "
            f"'{source_recipe_id}' has already been imported."
        )
        self.source = source
        self.source_recipe_id = source_recipe_id


class InvalidPipelineTransitionError(DomainError):
    """Raised when a raw recipe is moved to a pipeline stage it cannot reach
    from its current stage (see RawRecipe.tag/approve/reject/publish)."""

    def __init__(
        self, raw_recipe_id: str, current_stage: str, attempted_stage: str
    ) -> None:
        super().__init__(
            f"Raw recipe '{raw_recipe_id}' cannot move to '{attempted_stage}' "
            f"from its current stage '{current_stage}'."
        )
        self.raw_recipe_id = raw_recipe_id
        self.current_stage = current_stage
        self.attempted_stage = attempted_stage


class UnstorableLicenseError(DomainError):
    """Raised when publishing is blocked because a recipe's — or its
    image's — reported license isn't in the storable set (see License).
    Not legal advice; enforces the documented "free to store" policy."""

    def __init__(
        self, raw_recipe_id: str, reported_license: str, asset: str = "recipe"
    ) -> None:
        super().__init__(
            f"Raw recipe '{raw_recipe_id}' cannot be published: its {asset} "
            f"license '{reported_license}' is not in the storable set."
        )
        self.raw_recipe_id = raw_recipe_id
        self.reported_license = reported_license
        self.asset = asset
