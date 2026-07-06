"""Shared gap-computation plumbing for the Discover shopping-list use cases
(§5.4): GenerateShoppingListForRecipeUseCase (preview) and
AddShoppingListItemsUseCase (one-tap add) both need the exact same true
gaps for the exact same reason — the add action recomputes rather than
trusting a client-supplied list, so it must derive them identically to the
preview. This module is a plain helper, not a use case, so neither one
depends on the other directly.
"""

from __future__ import annotations

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.substitution_repository import SubstitutionRepository
from src.domain.services.shopping_list_generator import ShoppingListGenerator
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.substitution_context import SubstitutionContext

_CONTEXT = SubstitutionContext.GENERAL


async def compute_true_gaps(
    recipe: Recipe,
    user: User,
    user_id: str,
    inventory_item_repository: InventoryItemRepository,
    substitution_repository: SubstitutionRepository,
    ingredient_repository: IngredientRepository,
    shopping_list_generator: ShoppingListGenerator,
) -> tuple[list[str], dict[str, Ingredient]]:
    """Gather the user's current availability, the recipe's essential
    ingredients' substitution candidates, and the catalog entries needed to
    name them, then hand it all to ShoppingListGenerator.true_gaps.
    """
    inventory_items = await inventory_item_repository.list_by_user(user_id)
    available_ingredient_ids = {
        item.ingredient_id
        for item in inventory_items
        if item.quantity_state is not QuantityState.OUT
    }

    essential_ingredient_ids = {i.ingredient_id for i in recipe.essential_ingredients()}
    candidates_by_ingredient_id = {
        ingredient_id: await substitution_repository.find_for_ingredient(
            ingredient_id
        )
        for ingredient_id in essential_ingredient_ids
    }

    needed_ingredient_ids = set(essential_ingredient_ids)
    for candidates in candidates_by_ingredient_id.values():
        needed_ingredient_ids.update(c.to_ingredient_id for c in candidates)

    ingredients_by_id: dict[str, Ingredient] = {}
    for ingredient_id in needed_ingredient_ids:
        ingredient = await ingredient_repository.get_by_id(ingredient_id)
        if ingredient is not None:
            ingredients_by_id[ingredient_id] = ingredient

    gap_ingredient_ids = shopping_list_generator.true_gaps(
        recipe,
        user=user,
        available_ingredient_ids=available_ingredient_ids,
        context=_CONTEXT,
        candidates_by_ingredient_id=candidates_by_ingredient_id,
        ingredients_by_id=ingredients_by_id,
    )
    return gap_ingredient_ids, ingredients_by_id
