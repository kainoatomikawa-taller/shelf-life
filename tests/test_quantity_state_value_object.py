"""Unit tests for QuantityState.step_down (§5.6 AC3 — stock decrement)."""

from src.domain.value_objects.quantity_state import QuantityState


def test_in_steps_down_to_low() -> None:
    assert QuantityState.IN.step_down() is QuantityState.LOW


def test_low_steps_down_to_out() -> None:
    assert QuantityState.LOW.step_down() is QuantityState.OUT


def test_out_is_a_floor() -> None:
    assert QuantityState.OUT.step_down() is QuantityState.OUT
