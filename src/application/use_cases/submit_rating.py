"""SubmitRating use case (§5.6 AC1/AC2, §10 Step 5).

Backs the post-cook rating prompt: records a star/thumb rating plus optional
quick tags, folds it into the user's derived taste vector and the recipe's
global popularity_score (§10 Step 5's taste-profile learning loop), and
surfaces which of the recipe's ingredients are eligible for the optional
pantry stock decrement — without ever applying it. Applying the decrement is
a separate, explicit action (DecrementRecipeIngredientsUseCase) so the offer
is never forced.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.application.dtos.rating_dtos import SubmitRatingInput, SubmitRatingOutput
from src.application.mappers.rating_mapper import RatingMapper
from src.domain.entities.rating import Rating
from src.domain.exceptions import RecipeNotFoundError, UserNotFoundError
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.rating_repository import RatingRepository
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.recipe_stock_decrementer import RecipeStockDecrementer


class SubmitRatingUseCase:
    """Record a post-cook rating and offer (without applying) a stock
    decrement for the recipe's ingredients."""

    def __init__(
        self,
        rating_repository: RatingRepository,
        user_repository: UserRepository,
        recipe_repository: RecipeRepository,
        inventory_item_repository: InventoryItemRepository,
        stock_decrementer: RecipeStockDecrementer | None = None,
    ) -> None:
        self._rating_repository = rating_repository
        self._user_repository = user_repository
        self._recipe_repository = recipe_repository
        self._inventory_item_repository = inventory_item_repository
        self._stock_decrementer = stock_decrementer or RecipeStockDecrementer()

    async def execute(self, dto: SubmitRatingInput) -> SubmitRatingOutput:
        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        recipe = await self._recipe_repository.get_by_id(dto.recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(dto.recipe_id)

        rating = Rating(
            id=str(uuid.uuid4()),
            user_id=dto.user_id,
            recipe_id=dto.recipe_id,
            stars=dto.stars,
            made_it_at=datetime.now(UTC),
            quick_tags=dto.quick_tags,
        )
        await self._rating_repository.add(rating)

        user.record_rating(recipe.flavor_profile, float(dto.stars), dto.quick_tags)
        await self._user_repository.update(user)

        recipe.record_rating(float(dto.stars))
        await self._recipe_repository.update(recipe)

        inventory_items = await self._inventory_item_repository.list_by_user(
            dto.user_id
        )
        decrementable_items = self._stock_decrementer.find_decrementable_items(
            recipe, inventory_items
        )

        return RatingMapper.to_output(
            rating, [item.ingredient_id for item in decrementable_items]
        )
