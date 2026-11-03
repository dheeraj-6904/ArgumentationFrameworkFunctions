"""
tests/test_semantics_and_labelling.py

Unit tests for Component 2: Admissibility, Complete Extensions, Grounded Extension,
Preferred, Stable, Semi-Stable Extensions, Legal (in/out/undec) Labellings, and
Argument Acceptance Status (Items 5, 6A-6E).
"""

import pytest
from src.framework import ArgumentationFramework
from src.labelling import (
    IN,
    OUT,
    UNDEC,
    ArgumentLabelling,
    generate_legal_labellings,
    is_legal_labelling,
)
from src.semantics import (
    check_admissible_and_complete,
    compute_all_extensions,
    compute_complete_extensions,
    compute_grounded_extension,
    compute_preferred_extensions,
    compute_semi_stable_extensions,
    compute_stable_extensions,
    is_admissible,
    is_complete_extension,
    report_acceptance_status,
)


@pytest.fixture
def fig_5_1() -> ArgumentationFramework:
    """Book Figure 5.1: a3 -> a2 -> a1, a5 -> a4 -> a1."""
    return ArgumentationFramework(
        arguments=["a1", "a2", "a3", "a4", "a5"],
        attacks=[("a3", "a2"), ("a2", "a1"), ("a5", "a4"), ("a4", "a1")],
    )


@pytest.fixture
def fig_5_2() -> ArgumentationFramework:
    """Book Figure 5.2 (Example 5.7 & 5.8): a1 <-> a2, a3 unattacked."""
    return ArgumentationFramework(
        arguments=["a1", "a2", "a3"],
        attacks=[("a1", "a2"), ("a2", "a1")],
    )


def test_admissible_and_complete_fig_5_1(fig_5_1: ArgumentationFramework) -> None:
    # Book Example 5.5: empty, {a3}, {a5}, {a3, a5}, and {a1, a3, a5} are admissible
    for s in [set(), {"a3"}, {"a5"}, {"a3", "a5"}, {"a1", "a3", "a5"}]:
        assert is_admissible(fig_5_1, s) is True

    # {a1} alone is NOT admissible because it does not defend itself against a2, a4
    assert is_admissible(fig_5_1, {"a1"}) is False
    # {a1, a3} is NOT admissible because a4 is not defeated
    assert is_admissible(fig_5_1, {"a1", "a3"}) is False

    # Book Example 5.6: {a3, a5} is admissible but NOT complete because it defends a1
    res_a3_a5 = check_admissible_and_complete(fig_5_1, {"a3", "a5"})
    assert res_a3_a5 == {"is_admissible": True, "is_complete": False}
    assert is_complete_extension(fig_5_1, {"a3", "a5"}) is False

    # {a1, a3, a5} is both admissible and complete
    res_full = check_admissible_and_complete(fig_5_1, {"a1", "a3", "a5"})
    assert res_full == {"is_admissible": True, "is_complete": True}
    assert is_complete_extension(fig_5_1, {"a1", "a3", "a5"}) is True


def test_extensions_fig_5_1(fig_5_1: ArgumentationFramework) -> None:
    # Book Example 5.6 & 5.8: {a1, a3, a5} is the unique grounded, complete, preferred, stable, semi-stable extension
    assert compute_grounded_extension(fig_5_1) == {"a1", "a3", "a5"}
    assert compute_complete_extensions(fig_5_1) == [{"a1", "a3", "a5"}]
    assert compute_preferred_extensions(fig_5_1) == [{"a1", "a3", "a5"}]
    assert compute_stable_extensions(fig_5_1) == [{"a1", "a3", "a5"}]
    assert compute_semi_stable_extensions(fig_5_1) == [{"a1", "a3", "a5"}]


def test_extensions_fig_5_2(fig_5_2: ArgumentationFramework) -> None:
    # Book Example 5.7: Three complete extensions: {a3}, {a1, a3}, {a2, a3}
    complete = compute_complete_extensions(fig_5_2)
    assert complete == [{"a3"}, {"a1", "a3"}, {"a2", "a3"}]

    # Grounded extension is {a3}
    assert compute_grounded_extension(fig_5_2) == {"a3"}

    # Book Example 5.8: Two preferred extensions: {a1, a3} and {a2, a3}
    preferred = compute_preferred_extensions(fig_5_2)
    assert preferred == [{"a1", "a3"}, {"a2", "a3"}]

    # Stable and semi-stable extensions coincide with preferred here
    assert compute_stable_extensions(fig_5_2) == [{"a1", "a3"}, {"a2", "a3"}]
    assert compute_semi_stable_extensions(fig_5_2) == [{"a1", "a3"}, {"a2", "a3"}]


def test_semi_stable_vs_preferred_and_stable() -> None:
    """
    Test a framework where stable, semi-stable, and preferred extensions differ!
    Consider A = {a, b, c, d} with:
      - a <-> b (even cycle)
      - b -> c
      - c -> d, d -> c? No: let c -> c (self-loop), and b -> c!
    Let's trace:
      - Complete extensions:
        1. empty set: range = empty
        2. {a}: attacks {b}, so range({a}) = {a, b} (c is still undec because b is out and c->c)
        3. {b}: attacks {a, c}, so range({b}) = {a, b, c} = A!
      - Preferred extensions: {a} and {b} (both are maximal w.r.t. subseteq!).
      - Stable extensions: only {b} (since {a} does not attack c, whereas {b} attacks both a and c!).
      - Semi-stable extensions: only {b} (since range({b}) = {a, b, c} strictly contains range({a}) = {a, b}!).
    """
    af = ArgumentationFramework(
        arguments=["a", "b", "c"],
        attacks=[("a", "b"), ("b", "a"), ("b", "c"), ("c", "c")],
    )
    all_exts = compute_all_extensions(af)
    assert all_exts["grounded"] == [set()]
    assert all_exts["complete"] == [set(), {"a"}, {"b"}]
    assert all_exts["preferred"] == [{"a"}, {"b"}]
    assert all_exts["stable"] == [{"b"}]
    assert all_exts["semi_stable"] == [{"b"}]

    # Also test an odd 3-cycle where NO stable extension exists, but semi-stable exists!
    odd_cycle = ArgumentationFramework(
        arguments=["a", "b", "c"],
        attacks=[("a", "b"), ("b", "c"), ("c", "a")],
    )
    odd_exts = compute_all_extensions(odd_cycle)
    assert odd_exts["stable"] == []
    assert odd_exts["semi_stable"] == [set()]
    assert odd_exts["preferred"] == [set()]


def test_legal_labellings_fig_5_2(fig_5_2: ArgumentationFramework) -> None:
    # Book Figure 5.2: Three legal labellings L_G, L_1, L_2
    labellings = generate_legal_labellings(fig_5_2)
    assert len(labellings) == 3

    expected = [
        ArgumentLabelling({"a1": UNDEC, "a2": UNDEC, "a3": IN}),  # L_G
        ArgumentLabelling({"a1": IN, "a2": OUT, "a3": IN}),       # L_1
        ArgumentLabelling({"a1": OUT, "a2": IN, "a3": IN}),       # L_2
    ]
    assert labellings == expected

    # Verify illegal labelling is rejected
    illegal = {"a1": IN, "a2": IN, "a3": IN}
    assert is_legal_labelling(fig_5_2, illegal) is False


def test_acceptance_status(fig_5_1: ArgumentationFramework, fig_5_2: ArgumentationFramework) -> None:
    # Figure 5.1: a1, a3, a5 are skeptically accepted; a2, a4 are rejected
    assert report_acceptance_status(fig_5_1, "a1") == "skeptically accepted"
    assert report_acceptance_status(fig_5_1, "a3") == "skeptically accepted"
    assert report_acceptance_status(fig_5_1, "a2") == "rejected"
    assert report_acceptance_status(fig_5_1, "a4") == "rejected"

    # Figure 5.2: a3 is skeptically accepted; a1 and a2 are credulously accepted
    assert report_acceptance_status(fig_5_2, "a3") == "skeptically accepted"
    assert report_acceptance_status(fig_5_2, "a1") == "credulously accepted"
    assert report_acceptance_status(fig_5_2, "a2") == "credulously accepted"
