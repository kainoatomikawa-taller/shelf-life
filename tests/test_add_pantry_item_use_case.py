"""Use case tests using the in-memory repository (no DB required)."""

from datetime import date, timedelta

import pytest

from src.application.dtos.pantry_item_dtos import (
    AddPantryItemInput,
    ConsumePantryItemInput,
    ListPantryItemsInput,
)
from src.application.use_cases.add_pantry_item import AddPantryItemUseCase
from src.application.use_cases.consume_pantry_item import (
    ConsumePantryItemUseCase,
)
from src.application.use_cases.list_pantry_items import ListPantryItemsUseCase
from src.domain.exceptions import PantryItemNotFoundError
from src.domain.services.expiration_service import ExpirationService
from tests.fakes.in_memory_pantry_item_repository import (
    InMemoryPantryItemRepository,
)


@pytest.mark.asyncio
async def test_add_pantry_item() -> None:
    repo = InMemoryPantryItemRepository()
    use_case = AddPantryItemUseCase(repo)

    out = await use_case.execute(
        AddPantryItemInput(
            owner_id="user-1",
            name="Eggs",
            amount=12,
            unit="piece",
            expiration_date=date.today() + timedelta(days=14),
        )
    )

    assert out.name == "Eggs"
    assert out.freshness_status == "fresh"
    assert len(await repo.list_by_owner("user-1")) == 1


@pytest.mark.asyncio
async def test_list_orders_urgent_first() -> None:
    repo = InMemoryPantryItemRepository()
    add = AddPantryItemUseCase(repo)
    await add.execute(
        AddPantryItemInput("user-1", "Fresh", 1, "piece", date.today() + timedelta(days=30))
    )
    await add.execute(
        AddPantryItemInput("user-1", "Expired", 1, "piece", date.today() - timedelta(days=1))
    )

    list_uc = ListPantryItemsUseCase(repo, ExpirationService())
    items = await list_uc.execute(ListPantryItemsInput("user-1"))

    assert items[0].name == "Expired"


@pytest.mark.asyncio
async def test_consume_missing_item_raises() -> None:
    repo = InMemoryPantryItemRepository()
    use_case = ConsumePantryItemUseCase(repo)

    with pytest.raises(PantryItemNotFoundError):
        await use_case.execute(
            ConsumePantryItemInput(item_id="nope", amount=1, unit="piece")
        )
