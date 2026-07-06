"""Use case tests for SubmitRating (§5.6 AC1/AC2)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.rating_dtos import SubmitRatingInput
from src.application.use_cases.submit_rating import SubmitRatingUseCase
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.exceptions import RecipeNotFoundError, UserNotFoundError
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_inventory_item_repository import (
    InMemoryInventoryItemRepository,
)
from tests.fakes.in_memory_rating_repository import InMemoryRatingRepository
from tests.fakes.in_memory_recipe_repository import InMemoryRecipeRepository
from tests.fakes.in_memory_user_repository import InMemoryUserRepository

USER_ID = "user-1"
RECIPE_ID = "recipe-pancakes"
FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"


def _recipe() -> Recipe:
    return Recipe(
        id=RECIPE_ID,
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        flavor_profile=FlavorProfile(spiciness=0.9),
    )


def _inventory_item(
    ingredient_id: str, quantity_state: QuantityState
) -> InventoryItem:
    return InventoryItem(
        id=f"item-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        quantity_state=quantity_state,
        storage_location=StorageLocation.PANTRY,
        computed_freshness_date=datetime(2026, 1, 1, tzinfo=UTC).date(),
        freshness_date_type=FreshnessDateType.ESTIMATED_UNKNOWN,
        freshness_status=FreshnessDisplayStatus.FRESH,
        added_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def _build(inventory_items: list[InventoryItem]) -> tuple[
    SubmitRatingUseCase,
    InMemoryRatingRepository,
    InMemoryUserRepository,
    InMemoryInventoryItemRepository,
]:
    rating_repo = InMemoryRatingRepository()
    recipe_repo = InMemoryRecipeRepository([_recipe()])
    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)

    user_repo = InMemoryUserRepository()
    await user_repo.add(
        User(
            id=USER_ID,
            hard_constraints=HardConstraints(),
            preferences=SoftPreferences(),
        )
    )

    use_case = SubmitRatingUseCase(
        rating_repository=rating_repo,
        user_repository=user_repo,
        recipe_repository=recipe_repo,
        inventory_item_repository=inventory_repo,
    )
    return use_case, rating_repo, user_repo, inventory_repo


@pytest.mark.asyncio
async def test_captures_stars_and_quick_tags() -> None:
    use_case, repo, _, _ = await _build([])
    output = await use_case.execute(
        SubmitRatingInput(
            user_id=USER_ID,
            recipe_id=RECIPE_ID,
            stars=5,
            quick_tags=["loved it", "too spicy"],
        )
    )

    assert output.stars == 5
    assert output.quick_tags == ["loved it", "too spicy"]
    persisted = await repo.list_by_user(USER_ID)
    assert len(persisted) == 1


@pytest.mark.asyncio
async def test_quick_tags_are_optional() -> None:
    use_case, _, _, _ = await _build([])
    output = await use_case.execute(
        SubmitRatingInput(user_id=USER_ID, recipe_id=RECIPE_ID, stars=4)
    )
    assert output.quick_tags == []


@pytest.mark.asyncio
async def test_rating_updates_the_users_taste_vector() -> None:
    use_case, _, user_repo, _ = await _build([])
    before = (await user_repo.get_by_id(USER_ID)).taste_vector
    await use_case.execute(
        SubmitRatingInput(user_id=USER_ID, recipe_id=RECIPE_ID, stars=5)
    )
    after = (await user_repo.get_by_id(USER_ID)).taste_vector
    assert after != before


@pytest.mark.asyncio
async def test_offers_decrementable_ingredients_without_applying_them() -> None:
    use_case, _, _, inventory_repo = await _build(
        [
            _inventory_item(FLOUR, QuantityState.IN),
            _inventory_item(EGGS, QuantityState.OUT),
        ]
    )
    output = await use_case.execute(
        SubmitRatingInput(user_id=USER_ID, recipe_id=RECIPE_ID, stars=5)
    )

    assert output.decrementable_ingredient_ids == [FLOUR]

    persisted = {i.ingredient_id: i for i in await inventory_repo.list_by_user(USER_ID)}
    assert persisted[FLOUR].quantity_state == QuantityState.IN


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case, _, _, _ = await _build([])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            SubmitRatingInput(user_id="ghost", recipe_id=RECIPE_ID, stars=5)
        )


@pytest.mark.asyncio
async def test_unknown_recipe_raises_not_found() -> None:
    use_case, _, _, _ = await _build([])
    with pytest.raises(RecipeNotFoundError):
        await use_case.execute(
            SubmitRatingInput(user_id=USER_ID, recipe_id="ghost-recipe", stars=5)
        )
