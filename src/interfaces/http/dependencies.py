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

from src.application.use_cases.add_pantry_item import AddPantryItemUseCase
from src.application.use_cases.consume_pantry_item import (
    ConsumePantryItemUseCase,
)
from src.application.use_cases.list_pantry_items import ListPantryItemsUseCase
from src.domain.services.expiration_service import ExpirationService
from src.infrastructure.database.engine import get_session
from src.infrastructure.repositories.postgres_pantry_item_repository import (
    PostgresPantryItemRepository,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_repository(session: SessionDep) -> PostgresPantryItemRepository:
    return PostgresPantryItemRepository(session)


RepositoryDep = Annotated[
    PostgresPantryItemRepository, Depends(get_repository)
]


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
