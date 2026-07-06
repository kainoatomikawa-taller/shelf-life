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

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.add_inventory_item import AddInventoryItemUseCase
from src.application.use_cases.add_pantry_item import AddPantryItemUseCase
from src.application.use_cases.consume_pantry_item import (
    ConsumePantryItemUseCase,
)
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.list_inventory_items import ListInventoryItemsUseCase
from src.application.use_cases.list_pantry_items import ListPantryItemsUseCase
from src.application.use_cases.search_ingredients import SearchIngredientsUseCase
from src.application.use_cases.submit_onboarding import SubmitOnboardingUseCase
from src.domain.services.expiration_service import ExpirationService
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
