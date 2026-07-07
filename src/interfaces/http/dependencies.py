"""FastAPI dependency providers.

This module is the composition root for HTTP requests: the single place where
concrete implementations from the infrastructure layer are wired to the
abstractions the use cases depend on.

Composition roots are the one deliberate exception to the "interfaces must not
import infrastructure" guideline — dependency injection has to assemble the
graph *somewhere*. Every other file in `interfaces/` depends only on
`application/`. Keeping the wiring isolated here preserves that discipline.
"""

from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.cache_port import CachePort
from src.application.ports.token_verifier_port import (
    InvalidTokenError,
    TokenVerifierPort,
)
from src.application.use_cases.add_inventory_item import AddInventoryItemUseCase
from src.application.use_cases.add_pantry_item import AddPantryItemUseCase
from src.application.use_cases.add_purchases_to_kitchen import (
    AddPurchasesToKitchenUseCase,
)
from src.application.use_cases.add_shopping_list_items import (
    AddShoppingListItemsUseCase,
)
from src.application.use_cases.check_shopping_list_item import (
    CheckShoppingListItemUseCase,
)
from src.application.use_cases.consume_pantry_item import (
    ConsumePantryItemUseCase,
)
from src.application.use_cases.create_profile import CreateProfileUseCase
from src.application.use_cases.decrement_recipe_ingredients import (
    DecrementRecipeIngredientsUseCase,
)
from src.application.use_cases.generate_shopping_list_for_recipe import (
    GenerateShoppingListForRecipeUseCase,
)
from src.application.use_cases.get_cook_now_feed import GetCookNowFeedUseCase
from src.application.use_cases.get_discover_feed import GetDiscoverFeedUseCase
from src.application.use_cases.get_my_profile import GetMyProfileUseCase
from src.application.use_cases.get_recipe_detail import GetRecipeDetailUseCase
from src.application.use_cases.get_shopping_list import GetShoppingListUseCase
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.get_user_ratings import GetUserRatingsUseCase
from src.application.use_cases.list_inventory_items import ListInventoryItemsUseCase
from src.application.use_cases.list_pantry_items import ListPantryItemsUseCase
from src.application.use_cases.remove_inventory_item import RemoveInventoryItemUseCase
from src.application.use_cases.search_ingredients import SearchIngredientsUseCase
from src.application.use_cases.submit_onboarding import SubmitOnboardingUseCase
from src.application.use_cases.submit_rating import SubmitRatingUseCase
from src.application.use_cases.update_inventory_item_dates import (
    UpdateInventoryItemDatesUseCase,
)
from src.application.use_cases.update_inventory_item_quantity_state import (
    UpdateInventoryItemQuantityStateUseCase,
)
from src.application.use_cases.update_profile import UpdateProfileUseCase
from src.domain.services.expiration_service import ExpirationService
from src.infrastructure.auth.supabase_jwt_verifier import SupabaseJwtVerifier
from src.infrastructure.cache.redis_cache import RedisCache
from src.infrastructure.config import settings
from src.infrastructure.database.engine import get_session
from src.infrastructure.repositories.postgres_ingredient_repository import (
    PostgresIngredientRepository,
)
from src.infrastructure.repositories.postgres_inventory_item_repository import (
    PostgresInventoryItemRepository,
)
from src.infrastructure.repositories.postgres_pantry_item_repository import (
    PostgresPantryItemRepository,
)
from src.infrastructure.repositories.postgres_profile_repository import (
    PostgresProfileRepository,
)
from src.infrastructure.repositories.postgres_rating_repository import (
    PostgresRatingRepository,
)
from src.infrastructure.repositories.postgres_recipe_repository import (
    PostgresRecipeRepository,
)
from src.infrastructure.repositories.postgres_shopping_list_item_repository import (
    PostgresShoppingListItemRepository,
)
from src.infrastructure.repositories.postgres_substitution_repository import (
    PostgresSubstitutionRepository,
)
from src.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_repository(session: SessionDep) -> PostgresPantryItemRepository:
    return PostgresPantryItemRepository(session)


RepositoryDep = Annotated[
    PostgresPantryItemRepository, Depends(get_repository)
]


def get_user_repository(session: SessionDep) -> PostgresUserRepository:
    return PostgresUserRepository(session)


UserRepositoryDep = Annotated[PostgresUserRepository, Depends(get_user_repository)]


def get_add_use_case(repository: RepositoryDep) -> AddPantryItemUseCase:
    return AddPantryItemUseCase(repository)


def get_list_use_case(repository: RepositoryDep) -> ListPantryItemsUseCase:
    return ListPantryItemsUseCase(repository, ExpirationService())


def get_consume_use_case(
    repository: RepositoryDep,
) -> ConsumePantryItemUseCase:
    return ConsumePantryItemUseCase(repository)


AddUseCaseDep = Annotated[AddPantryItemUseCase, Depends(get_add_use_case)]
ListUseCaseDep = Annotated[ListPantryItemsUseCase, Depends(get_list_use_case)]
ConsumeUseCaseDep = Annotated[
    ConsumePantryItemUseCase, Depends(get_consume_use_case)
]


def get_submit_onboarding_use_case(
    repository: UserRepositoryDep,
) -> SubmitOnboardingUseCase:
    return SubmitOnboardingUseCase(repository)


SubmitOnboardingUseCaseDep = Annotated[
    SubmitOnboardingUseCase, Depends(get_submit_onboarding_use_case)
]


def get_user_profile_use_case(
    repository: UserRepositoryDep,
) -> GetUserProfileUseCase:
    return GetUserProfileUseCase(repository)


GetUserProfileUseCaseDep = Annotated[
    GetUserProfileUseCase, Depends(get_user_profile_use_case)
]


def get_ingredient_repository(
    session: SessionDep,
) -> PostgresIngredientRepository:
    return PostgresIngredientRepository(session)


IngredientRepositoryDep = Annotated[
    PostgresIngredientRepository, Depends(get_ingredient_repository)
]


def get_inventory_item_repository(
    session: SessionDep,
) -> PostgresInventoryItemRepository:
    return PostgresInventoryItemRepository(session)


InventoryItemRepositoryDep = Annotated[
    PostgresInventoryItemRepository, Depends(get_inventory_item_repository)
]


def get_search_ingredients_use_case(
    repository: IngredientRepositoryDep,
) -> SearchIngredientsUseCase:
    return SearchIngredientsUseCase(repository)


SearchIngredientsUseCaseDep = Annotated[
    SearchIngredientsUseCase, Depends(get_search_ingredients_use_case)
]


def get_add_inventory_item_use_case(
    inventory_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
) -> AddInventoryItemUseCase:
    return AddInventoryItemUseCase(inventory_repository, ingredient_repository)


AddInventoryItemUseCaseDep = Annotated[
    AddInventoryItemUseCase, Depends(get_add_inventory_item_use_case)
]


def get_list_inventory_items_use_case(
    inventory_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
) -> ListInventoryItemsUseCase:
    return ListInventoryItemsUseCase(inventory_repository, ingredient_repository)


ListInventoryItemsUseCaseDep = Annotated[
    ListInventoryItemsUseCase, Depends(get_list_inventory_items_use_case)
]


def get_update_inventory_item_quantity_state_use_case(
    inventory_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
) -> UpdateInventoryItemQuantityStateUseCase:
    return UpdateInventoryItemQuantityStateUseCase(
        inventory_repository, ingredient_repository
    )


UpdateInventoryItemQuantityStateUseCaseDep = Annotated[
    UpdateInventoryItemQuantityStateUseCase,
    Depends(get_update_inventory_item_quantity_state_use_case),
]


def get_update_inventory_item_dates_use_case(
    inventory_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
) -> UpdateInventoryItemDatesUseCase:
    return UpdateInventoryItemDatesUseCase(
        inventory_repository, ingredient_repository
    )


UpdateInventoryItemDatesUseCaseDep = Annotated[
    UpdateInventoryItemDatesUseCase, Depends(get_update_inventory_item_dates_use_case)
]


def get_remove_inventory_item_use_case(
    inventory_repository: InventoryItemRepositoryDep,
) -> RemoveInventoryItemUseCase:
    return RemoveInventoryItemUseCase(inventory_repository)


RemoveInventoryItemUseCaseDep = Annotated[
    RemoveInventoryItemUseCase, Depends(get_remove_inventory_item_use_case)
]


def get_recipe_repository(session: SessionDep) -> PostgresRecipeRepository:
    return PostgresRecipeRepository(session)


RecipeRepositoryDep = Annotated[
    PostgresRecipeRepository, Depends(get_recipe_repository)
]


def get_substitution_repository(
    session: SessionDep,
) -> PostgresSubstitutionRepository:
    return PostgresSubstitutionRepository(session)


SubstitutionRepositoryDep = Annotated[
    PostgresSubstitutionRepository, Depends(get_substitution_repository)
]


def get_cook_now_feed_use_case(
    recipe_repository: RecipeRepositoryDep,
    substitution_repository: SubstitutionRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    user_repository: UserRepositoryDep,
) -> GetCookNowFeedUseCase:
    return GetCookNowFeedUseCase(
        recipe_repository=recipe_repository,
        substitution_repository=substitution_repository,
        ingredient_repository=ingredient_repository,
        inventory_item_repository=inventory_item_repository,
        user_repository=user_repository,
    )


GetCookNowFeedUseCaseDep = Annotated[
    GetCookNowFeedUseCase, Depends(get_cook_now_feed_use_case)
]


def get_shopping_list_item_repository(
    session: SessionDep,
) -> PostgresShoppingListItemRepository:
    return PostgresShoppingListItemRepository(session)


ShoppingListItemRepositoryDep = Annotated[
    PostgresShoppingListItemRepository, Depends(get_shopping_list_item_repository)
]


def get_discover_feed_use_case(
    recipe_repository: RecipeRepositoryDep,
    substitution_repository: SubstitutionRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    user_repository: UserRepositoryDep,
) -> GetDiscoverFeedUseCase:
    return GetDiscoverFeedUseCase(
        recipe_repository=recipe_repository,
        substitution_repository=substitution_repository,
        ingredient_repository=ingredient_repository,
        inventory_item_repository=inventory_item_repository,
        user_repository=user_repository,
    )


GetDiscoverFeedUseCaseDep = Annotated[
    GetDiscoverFeedUseCase, Depends(get_discover_feed_use_case)
]


def get_recipe_detail_use_case(
    recipe_repository: RecipeRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
) -> GetRecipeDetailUseCase:
    return GetRecipeDetailUseCase(
        recipe_repository=recipe_repository,
        ingredient_repository=ingredient_repository,
    )


GetRecipeDetailUseCaseDep = Annotated[
    GetRecipeDetailUseCase, Depends(get_recipe_detail_use_case)
]


def get_generate_shopping_list_for_recipe_use_case(
    recipe_repository: RecipeRepositoryDep,
    substitution_repository: SubstitutionRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    user_repository: UserRepositoryDep,
) -> GenerateShoppingListForRecipeUseCase:
    return GenerateShoppingListForRecipeUseCase(
        recipe_repository=recipe_repository,
        substitution_repository=substitution_repository,
        ingredient_repository=ingredient_repository,
        inventory_item_repository=inventory_item_repository,
        user_repository=user_repository,
    )


GenerateShoppingListForRecipeUseCaseDep = Annotated[
    GenerateShoppingListForRecipeUseCase,
    Depends(get_generate_shopping_list_for_recipe_use_case),
]


def get_add_shopping_list_items_use_case(
    recipe_repository: RecipeRepositoryDep,
    substitution_repository: SubstitutionRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    user_repository: UserRepositoryDep,
    shopping_list_item_repository: ShoppingListItemRepositoryDep,
) -> AddShoppingListItemsUseCase:
    return AddShoppingListItemsUseCase(
        recipe_repository=recipe_repository,
        substitution_repository=substitution_repository,
        ingredient_repository=ingredient_repository,
        inventory_item_repository=inventory_item_repository,
        user_repository=user_repository,
        shopping_list_item_repository=shopping_list_item_repository,
    )


AddShoppingListItemsUseCaseDep = Annotated[
    AddShoppingListItemsUseCase, Depends(get_add_shopping_list_items_use_case)
]


def get_get_shopping_list_use_case(
    shopping_list_item_repository: ShoppingListItemRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    user_repository: UserRepositoryDep,
) -> GetShoppingListUseCase:
    return GetShoppingListUseCase(
        shopping_list_item_repository=shopping_list_item_repository,
        inventory_item_repository=inventory_item_repository,
        ingredient_repository=ingredient_repository,
        user_repository=user_repository,
    )


GetShoppingListUseCaseDep = Annotated[
    GetShoppingListUseCase, Depends(get_get_shopping_list_use_case)
]


def get_check_shopping_list_item_use_case(
    shopping_list_item_repository: ShoppingListItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
) -> CheckShoppingListItemUseCase:
    return CheckShoppingListItemUseCase(
        shopping_list_item_repository=shopping_list_item_repository,
        ingredient_repository=ingredient_repository,
    )


CheckShoppingListItemUseCaseDep = Annotated[
    CheckShoppingListItemUseCase, Depends(get_check_shopping_list_item_use_case)
]


def get_add_purchases_to_kitchen_use_case(
    shopping_list_item_repository: ShoppingListItemRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    user_repository: UserRepositoryDep,
) -> AddPurchasesToKitchenUseCase:
    return AddPurchasesToKitchenUseCase(
        shopping_list_item_repository=shopping_list_item_repository,
        inventory_item_repository=inventory_item_repository,
        ingredient_repository=ingredient_repository,
        user_repository=user_repository,
    )


AddPurchasesToKitchenUseCaseDep = Annotated[
    AddPurchasesToKitchenUseCase, Depends(get_add_purchases_to_kitchen_use_case)
]


def get_rating_repository(session: SessionDep) -> PostgresRatingRepository:
    return PostgresRatingRepository(session)


RatingRepositoryDep = Annotated[
    PostgresRatingRepository, Depends(get_rating_repository)
]


def get_submit_rating_use_case(
    rating_repository: RatingRepositoryDep,
    user_repository: UserRepositoryDep,
    recipe_repository: RecipeRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
) -> SubmitRatingUseCase:
    return SubmitRatingUseCase(
        rating_repository=rating_repository,
        user_repository=user_repository,
        recipe_repository=recipe_repository,
        inventory_item_repository=inventory_item_repository,
    )


SubmitRatingUseCaseDep = Annotated[
    SubmitRatingUseCase, Depends(get_submit_rating_use_case)
]


def get_get_user_ratings_use_case(
    rating_repository: RatingRepositoryDep,
    user_repository: UserRepositoryDep,
) -> GetUserRatingsUseCase:
    return GetUserRatingsUseCase(
        rating_repository=rating_repository,
        user_repository=user_repository,
    )


GetUserRatingsUseCaseDep = Annotated[
    GetUserRatingsUseCase, Depends(get_get_user_ratings_use_case)
]


def get_decrement_recipe_ingredients_use_case(
    recipe_repository: RecipeRepositoryDep,
    inventory_item_repository: InventoryItemRepositoryDep,
    ingredient_repository: IngredientRepositoryDep,
    user_repository: UserRepositoryDep,
) -> DecrementRecipeIngredientsUseCase:
    return DecrementRecipeIngredientsUseCase(
        recipe_repository=recipe_repository,
        inventory_item_repository=inventory_item_repository,
        ingredient_repository=ingredient_repository,
        user_repository=user_repository,
    )


DecrementRecipeIngredientsUseCaseDep = Annotated[
    DecrementRecipeIngredientsUseCase,
    Depends(get_decrement_recipe_ingredients_use_case),
]


# --- Auth: Supabase JWT verification ------------------------------------

_cache = RedisCache()
_jwks_http_client = httpx.AsyncClient()
_bearer_scheme = HTTPBearer()


def get_cache() -> CachePort:
    return _cache


CacheDep = Annotated[CachePort, Depends(get_cache)]


def get_token_verifier(cache: CacheDep) -> TokenVerifierPort:
    return SupabaseJwtVerifier(
        supabase_url=settings.supabase_url,
        audience=settings.supabase_jwt_audience,
        cache=cache,
        http_client=_jwks_http_client,
        cache_ttl_seconds=settings.supabase_jwks_cache_ttl_seconds,
    )


TokenVerifierDep = Annotated[TokenVerifierPort, Depends(get_token_verifier)]

BearerCredentialsDep = Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)]


async def get_current_user_id(
    credentials: BearerCredentialsDep, verifier: TokenVerifierDep
) -> str:
    try:
        return await verifier.verify(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]


async def get_authenticated_session(
    session: SessionDep, current_user_id: CurrentUserIdDep
) -> AsyncSession:
    """A DB session with the RLS identity claim set to the verified caller.

    Repositories for user-owned tables (profiles, users/taste-profile,
    inventory_items, ratings, shopping_list_items) must depend on this
    instead of `SessionDep` — Postgres RLS policies check
    `auth.uid()`, which reads this session-local setting. `is_local=false`
    (session-scoped, not transaction-local) is deliberate: some repositories
    commit mid-request, and a transaction-local setting would be dropped by
    that commit for any query issued afterward in the same session.
    """
    await session.execute(
        text("SELECT set_config('request.jwt.claim.sub', :sub, false)"),
        {"sub": current_user_id},
    )
    return session


AuthenticatedSessionDep = Annotated[
    AsyncSession, Depends(get_authenticated_session)
]


# --- Profiles -------------------------------------------------------------


def get_profile_repository(
    session: AuthenticatedSessionDep,
) -> PostgresProfileRepository:
    return PostgresProfileRepository(session)


ProfileRepositoryDep = Annotated[
    PostgresProfileRepository, Depends(get_profile_repository)
]


def get_create_profile_use_case(
    repository: ProfileRepositoryDep,
) -> CreateProfileUseCase:
    return CreateProfileUseCase(repository)


CreateProfileUseCaseDep = Annotated[
    CreateProfileUseCase, Depends(get_create_profile_use_case)
]


def get_my_profile_use_case(
    repository: ProfileRepositoryDep,
) -> GetMyProfileUseCase:
    return GetMyProfileUseCase(repository)


GetMyProfileUseCaseDep = Annotated[
    GetMyProfileUseCase, Depends(get_my_profile_use_case)
]


def get_update_profile_use_case(
    repository: ProfileRepositoryDep,
) -> UpdateProfileUseCase:
    return UpdateProfileUseCase(repository)


UpdateProfileUseCaseDep = Annotated[
    UpdateProfileUseCase, Depends(get_update_profile_use_case)
]
