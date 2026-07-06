"""InventoryItem entity.

Represents a single item a user has in their pantry, fridge or freezer, per
§8. Unlike PantryItem's precise Quantity, stock is tracked as a coarse
QuantityState (in/low/out) — a lower-friction signal for users who won't
weigh or count what they have.

The entity does not compute its own freshness fields inline the way
PantryItem does. Freshness date resolution needs an ingredient's shelf life
and category, which live on the Ingredient entity rather than on the item
itself, so computedFreshnessDate/freshnessDateType/freshnessStatus are
populated by the freshness engine (FreshnessCalculator +
FreshnessStatusResolver) via the `create` factory and `refresh_freshness`,
and stored on the entity rather than recomputed on every read.
"""

from __future__ import annotations

from datetime import date, datetime

from src.domain.entities.ingredient import Ingredient
from src.domain.exceptions import ValidationError
from src.domain.services.freshness_calculator import FreshnessCalculator
from src.domain.services.freshness_status_resolver import FreshnessStatusResolver
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.freshness_input import FreshnessInput
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.storage_location import StorageLocation


class InventoryItem:
    """A user's pantry/fridge/freezer item, with derived freshness state."""

    def __init__(
        self,
        id: str,
        user_id: str,
        ingredient_id: str,
        quantity_state: QuantityState,
        storage_location: StorageLocation,
        computed_freshness_date: date,
        freshness_date_type: FreshnessDateType,
        freshness_status: FreshnessDisplayStatus,
        added_at: datetime,
        purchase_date: date | None = None,
        printed_package_date: date | None = None,
        is_frozen: bool = False,
        notes: str | None = None,
    ) -> None:
        if not id:
            raise ValidationError("InventoryItem id is required.")
        if not user_id:
            raise ValidationError("InventoryItem user_id is required.")
        if not ingredient_id:
            raise ValidationError("InventoryItem ingredient_id is required.")
        if not isinstance(quantity_state, QuantityState):
            raise ValidationError(
                "InventoryItem quantity_state must be a valid QuantityState."
            )
        if not isinstance(storage_location, StorageLocation):
            raise ValidationError(
                "InventoryItem storage_location must be a valid StorageLocation."
            )

        self._id = id
        self._user_id = user_id
        self._ingredient_id = ingredient_id
        self._quantity_state = quantity_state
        self._storage_location = storage_location
        self._purchase_date = purchase_date
        self._printed_package_date = printed_package_date
        self._is_frozen = is_frozen
        self._computed_freshness_date = computed_freshness_date
        self._freshness_date_type = freshness_date_type
        self._freshness_status = freshness_status
        self._added_at = added_at
        self._notes = notes

    # --- Identity & read-only accessors -------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def ingredient_id(self) -> str:
        return self._ingredient_id

    @property
    def quantity_state(self) -> QuantityState:
        return self._quantity_state

    @property
    def storage_location(self) -> StorageLocation:
        return self._storage_location

    @property
    def purchase_date(self) -> date | None:
        return self._purchase_date

    @property
    def printed_package_date(self) -> date | None:
        return self._printed_package_date

    @property
    def is_frozen(self) -> bool:
        return self._is_frozen

    @property
    def computed_freshness_date(self) -> date:
        return self._computed_freshness_date

    @property
    def freshness_date_type(self) -> FreshnessDateType:
        return self._freshness_date_type

    @property
    def freshness_status(self) -> FreshnessDisplayStatus:
        return self._freshness_status

    @property
    def added_at(self) -> datetime:
        return self._added_at

    @property
    def notes(self) -> str | None:
        return self._notes

    # --- Construction --------------------------------------------------------

    @classmethod
    def create(
        cls,
        id: str,
        user_id: str,
        ingredient: Ingredient,
        quantity_state: QuantityState,
        storage_location: StorageLocation,
        added_at: datetime,
        today: date,
        purchase_date: date | None = None,
        printed_package_date: date | None = None,
        is_frozen: bool = False,
        notes: str | None = None,
        calculator: FreshnessCalculator | None = None,
        status_resolver: FreshnessStatusResolver | None = None,
    ) -> "InventoryItem":
        """Build an item with its derived freshness fields populated by the
        freshness engine, from the given ingredient's shelf life and category.
        """
        freshness_date, date_type, status = _compute_freshness(
            ingredient=ingredient,
            storage_location=storage_location,
            purchase_date=purchase_date,
            printed_package_date=printed_package_date,
            is_frozen=is_frozen,
            today=today,
            calculator=calculator or FreshnessCalculator(),
            status_resolver=status_resolver or FreshnessStatusResolver(),
        )
        return cls(
            id=id,
            user_id=user_id,
            ingredient_id=ingredient.id,
            quantity_state=quantity_state,
            storage_location=storage_location,
            computed_freshness_date=freshness_date,
            freshness_date_type=date_type,
            freshness_status=status,
            added_at=added_at,
            purchase_date=purchase_date,
            printed_package_date=printed_package_date,
            is_frozen=is_frozen,
            notes=notes,
        )

    # --- Behaviour (business rules live here) -------------------------------

    def update_quantity_state(self, quantity_state: QuantityState) -> None:
        if not isinstance(quantity_state, QuantityState):
            raise ValidationError(
                "InventoryItem quantity_state must be a valid QuantityState."
            )
        self._quantity_state = quantity_state

    def update_notes(self, notes: str | None) -> None:
        self._notes = notes

    def refresh_freshness(
        self,
        ingredient: Ingredient,
        today: date,
        calculator: FreshnessCalculator | None = None,
        status_resolver: FreshnessStatusResolver | None = None,
        thawed_at: date | None = None,
    ) -> None:
        """Recompute the derived freshness fields via the freshness engine.

        Call after anything that can change the resolved freshness date:
        a storage move, freezing, or thawing.
        """
        freshness_date, date_type, status = _compute_freshness(
            ingredient=ingredient,
            storage_location=self._storage_location,
            purchase_date=self._purchase_date,
            printed_package_date=self._printed_package_date,
            is_frozen=self._is_frozen,
            today=today,
            calculator=calculator or FreshnessCalculator(),
            status_resolver=status_resolver or FreshnessStatusResolver(),
            thawed_at=thawed_at,
        )
        self._computed_freshness_date = freshness_date
        self._freshness_date_type = date_type
        self._freshness_status = status

    def update_dates(
        self,
        ingredient: Ingredient,
        today: date,
        purchase_date: date | None = None,
        printed_package_date: date | None = None,
        calculator: FreshnessCalculator | None = None,
        status_resolver: FreshnessStatusResolver | None = None,
    ) -> None:
        """Correct the purchase and/or printed package date (the "edit
        dates" quick action, §5.2) and recompute freshness to match.
        """
        self._purchase_date = purchase_date
        self._printed_package_date = printed_package_date
        self.refresh_freshness(ingredient, today, calculator, status_resolver)

    def move_storage(
        self,
        storage_location: StorageLocation,
        ingredient: Ingredient,
        today: date,
        calculator: FreshnessCalculator | None = None,
        status_resolver: FreshnessStatusResolver | None = None,
    ) -> None:
        """Change storage location and recompute freshness for the new home."""
        if not isinstance(storage_location, StorageLocation):
            raise ValidationError(
                "InventoryItem storage_location must be a valid StorageLocation."
            )
        self._storage_location = storage_location
        self.refresh_freshness(ingredient, today, calculator, status_resolver)

    def mark_thawed(
        self,
        thawed_at: date,
        ingredient: Ingredient,
        today: date,
        calculator: FreshnessCalculator | None = None,
        status_resolver: FreshnessStatusResolver | None = None,
    ) -> None:
        """Mark the item as thawed and fold the thaw safety window into the
        resolved freshness date. thawed_at is not retained as a field — once
        applied, it's baked into computed_freshness_date.
        """
        self._is_frozen = False
        self.refresh_freshness(
            ingredient, today, calculator, status_resolver, thawed_at=thawed_at
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InventoryItem):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)


def _compute_freshness(
    ingredient: Ingredient,
    storage_location: StorageLocation,
    purchase_date: date | None,
    printed_package_date: date | None,
    is_frozen: bool,
    today: date,
    calculator: FreshnessCalculator,
    status_resolver: FreshnessStatusResolver,
    thawed_at: date | None = None,
) -> tuple[date, FreshnessDateType, FreshnessDisplayStatus]:
    freshness_input = FreshnessInput(
        package_date=printed_package_date,
        purchase_date=purchase_date,
        storage_shelf_life_days=ingredient.typical_shelf_life.for_location(
            storage_location
        ),
        freezer_shelf_life_days=ingredient.typical_shelf_life.freezer_days,
        is_frozen=is_frozen,
        thawed_at=thawed_at,
    )
    result = calculator.compute_freshness(freshness_input, today)
    status = status_resolver.derive_status(
        result.freshness_date, today, ingredient.category
    )
    return result.freshness_date, result.freshness_date_type, status
