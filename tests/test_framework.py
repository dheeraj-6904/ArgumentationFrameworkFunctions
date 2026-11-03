"""
tests/test_framework.py

Unit tests for Component 1: ArgumentationFramework, conflict-freeness,
defense of an argument, and the characteristic function F_AF(S).
Tested on Figure 5.1 and Figure 5.2 from Chapter 5 ("Argumentation among Agents"
by Iyad Rahwan in Multiagent Systems, 2nd ed., Gerhard Weiss).
"""

import pytest
from src.framework import (
    ArgumentationFramework,
    characteristic_function,
    is_conflict_free,
    is_defended_by,
)


@pytest.fixture
def fig_5_1() -> ArgumentationFramework:
    """
    Book Figure 5.1:
    Arguments: {a1, a2, a3, a4, a5}
    Attacks: a3 -> a2, a2 -> a1, a5 -> a4, a4 -> a1
    """
    args = ["a1", "a2", "a3", "a4", "a5"]
    attacks = [("a3", "a2"), ("a2", "a1"), ("a5", "a4"), ("a4", "a1")]
    return ArgumentationFramework(arguments=args, attacks=attacks)


@pytest.fixture
def fig_5_2() -> ArgumentationFramework:
    """
    Book Figure 5.2 (Example 5.7):
    Arguments: {a1, a2, a3}
    Attacks: a1 <-> a2 (mutual attack), a3 unattacked
    """
    args = ["a1", "a2", "a3"]
    attacks = [("a1", "a2"), ("a2", "a1")]
    return ArgumentationFramework(arguments=args, attacks=attacks)


def test_framework_creation_and_queries(fig_5_1: ArgumentationFramework) -> None:
    assert fig_5_1.arguments == frozenset({"a1", "a2", "a3", "a4", "a5"})
    assert fig_5_1.attackers_of("a1") == frozenset({"a2", "a4"})
    assert fig_5_1.attackers_of("a3") == frozenset()
    assert fig_5_1.attacked_by("a3") == frozenset({"a2"})
    assert fig_5_1.set_attacked_by({"a3", "a5"}) == frozenset({"a2", "a4"})


def test_is_conflict_free(fig_5_1: ArgumentationFramework, fig_5_2: ArgumentationFramework) -> None:
    # Empty set and unattacking sets are conflict-free
    assert is_conflict_free(fig_5_1, set()) is True
    assert is_conflict_free(fig_5_1, {"a3", "a5"}) is True
    assert is_conflict_free(fig_5_1, {"a1", "a3", "a5"}) is True
    assert is_conflict_free(fig_5_1, {"a2", "a4"}) is True

    # Sets with internal attacks are not conflict-free
    assert is_conflict_free(fig_5_1, {"a1", "a2"}) is False
    assert is_conflict_free(fig_5_1, {"a2", "a3"}) is False
    assert is_conflict_free(fig_5_2, {"a1", "a2"}) is False
    assert is_conflict_free(fig_5_2, {"a1", "a3"}) is True

    # Self-attacking argument
    self_loop_af = ArgumentationFramework(["x"], [("x", "x")])
    assert is_conflict_free(self_loop_af, {"x"}) is False


def test_is_defended_by(fig_5_1: ArgumentationFramework) -> None:
    # Example 5.5 in the book:
    # a3 and a5 have no attackers, so they are defended by the empty set
    assert is_defended_by(fig_5_1, "a3", set()) is True
    assert is_defended_by(fig_5_1, "a5", set()) is True
    assert is_defended_by(fig_5_1, "a1", set()) is False

    # {a3} only defeats a2, not a4, so {a3} alone does NOT defend a1
    assert is_defended_by(fig_5_1, "a1", {"a3"}) is False
    # {a3, a5} defeats both a2 and a4, so {a3, a5} defends a1
    assert is_defended_by(fig_5_1, "a1", {"a3", "a5"}) is True
    assert is_defended_by(fig_5_1, "a1", {"a1", "a3", "a5"}) is True


def test_characteristic_function(fig_5_1: ArgumentationFramework, fig_5_2: ArgumentationFramework) -> None:
    # Example 5.6 in the book:
    # F(empty) = {a3, a5}
    assert characteristic_function(fig_5_1, set()) == {"a3", "a5"}
    # F({a3}) = {a3, a5}
    assert characteristic_function(fig_5_1, {"a3"}) == {"a3", "a5"}
    # F({a3, a5}) = {a1, a3, a5}
    assert characteristic_function(fig_5_1, {"a3", "a5"}) == {"a1", "a3", "a5"}
    # F({a1, a3, a5}) = {a1, a3, a5} (fixed point!)
    assert characteristic_function(fig_5_1, {"a1", "a3", "a5"}) == {"a1", "a3", "a5"}

    # Figure 5.2:
    assert characteristic_function(fig_5_2, set()) == {"a3"}
    assert characteristic_function(fig_5_2, {"a3"}) == {"a3"}
    assert characteristic_function(fig_5_2, {"a1", "a3"}) == {"a1", "a3"}
    assert characteristic_function(fig_5_2, {"a2", "a3"}) == {"a2", "a3"}
