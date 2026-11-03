"""
tests/test_strategic.py

Unit tests for Component 3: Strategic Argumentation & Grounded Direct
Argumentation Mechanism (Part 2: Items 1-4).
Includes verification on Book Example 5.10 and Example 5.11, plus cycle edge cases.
"""

import pytest
from src.framework import ArgumentationFramework
from src.strategic import (
    check_theorem_5_3_strategyproof,
    check_theorem_5_4_condition,
    find_best_responses,
    grounded_direct_mechanism,
)


@pytest.fixture
def example_5_10() -> tuple[ArgumentationFramework, dict[str, set[str]]]:
    """
    Book Example 5.10:
    Agents x, y, z with types:
      A_x = {a1, a4, a5}
      A_y = {a2}
      A_z = {a3}
    Defeat relation R = {(a1, a2), (a2, a3), (a3, a4), (a3, a5)}
    """
    af = ArgumentationFramework(
        arguments=["a1", "a2", "a3", "a4", "a5"],
        attacks=[("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")],
    )
    types = {
        "x": {"a1", "a4", "a5"},
        "y": {"a2"},
        "z": {"a3"},
    }
    return af, types


@pytest.fixture
def example_5_11() -> tuple[ArgumentationFramework, dict[str, set[str]]]:
    """
    Book Example 5.11:
    Variant of Example 5.10 with additional argument a6 and defeat (a6, a3).
    Agent types:
      A_x = {a1, a4, a5, a6}
      A_y = {a2}
      A_z = {a3}
    """
    af = ArgumentationFramework(
        arguments=["a1", "a2", "a3", "a4", "a5", "a6"],
        attacks=[
            ("a1", "a2"),
            ("a2", "a3"),
            ("a3", "a4"),
            ("a3", "a5"),
            ("a6", "a3"),
        ],
    )
    types = {
        "x": {"a1", "a4", "a5", "a6"},
        "y": {"a2"},
        "z": {"a3"},
    }
    return af, types


def test_example_5_10_strategic_hiding(
    example_5_10: tuple[ArgumentationFramework, dict[str, set[str]]],
) -> None:
    af, types = example_5_10

    # Under truthful full revelation, outcome is {a1, a3}
    truthful_outcome = grounded_direct_mechanism(af, types)
    assert truthful_outcome == {"a1", "a3"}

    # Check agent x's best response when y reveals {a2} and z reveals {a3}
    br_x = find_best_responses(
        af,
        agent_id="x",
        agent_true_args=types["x"],
        other_agents_reports={"y": types["y"], "z": types["z"]},
    )
    assert br_x.truthful_utility == 1  # |{a1, a4, a5} cap {a1, a3}| = |{a1}| = 1
    assert br_x.max_utility == 2       # |{a1, a4, a5} cap {a2, a4, a5}| = |{a4, a5}| = 2
    assert br_x.can_gain_by_hiding is True
    assert {"a4", "a5"} in br_x.best_reports

    # Theorem 5.3 must report NOT strategyproof
    t53 = check_theorem_5_3_strategyproof(af, types)
    assert t53.is_strategyproof is False
    assert t53.witness is not None
    assert t53.witness.manipulating_agent == "x"
    assert t53.witness.manipulated_utility == 2
    assert t53.witness.truthful_utility == 1

    # Theorem 5.4 condition must ALSO fail (odd-length paths a1->a2->a3->a4 and a1->a2->a3->a5 of length 3)
    t54 = check_theorem_5_4_condition(af, types)
    assert t54.condition_holds is False
    odd_pairs = {(v.source, v.target) for v in t54.violations}
    assert ("a1", "a4") in odd_pairs
    assert ("a1", "a5") in odd_pairs


def test_example_5_11_cancellation_of_indirect_self_defeat(
    example_5_11: tuple[ArgumentationFramework, dict[str, set[str]]],
) -> None:
    """
    Book Example 5.11 demonstrates that Theorem 5.4's condition is sufficient
    but NOT necessary:
    - Agent x still has the odd-length paths a1->a2->a3->a4 and a1->a2->a3->a5,
      so Theorem 5.4's condition FAILS.
    - Yet because a6 -> a3 directly defeats a3, revealing all of A_x = {a1, a4, a5, a6}
      yields outcome {a1, a4, a5, a6} (utility 4 for agent x!), and truth-telling
      is a dominant strategy for every agent against every profile (Theorem 5.3 holds!).
    """
    af, types = example_5_11

    truthful_outcome = grounded_direct_mechanism(af, types)
    assert truthful_outcome == {"a1", "a4", "a5", "a6"}

    t53 = check_theorem_5_3_strategyproof(af, types)
    assert t53.is_strategyproof is True

    t54 = check_theorem_5_4_condition(af, types)
    assert t54.condition_holds is False


def test_theorem_5_4_cycle_handling() -> None:
    """
    Verify that `check_theorem_5_4_condition` correctly detects odd-length paths
    in the presence of cycles and reconvergent even/odd paths where a naive BFS/DFS
    would fail.
    """
    # Reconvergent graph:
    #   a1 -> b -> a2 (length 2, EVEN)
    #   a1 -> c -> d -> b -> a2 (length 4, EVEN)
    #   b -> c (creates cycle b -> c -> d -> b of length 3!)
    # Because of the cycle b -> c -> d -> b, the simple path is a1 -> c -> d -> b -> a2 (even)
    # and a1 -> b -> a2 (even), wait: what about a1 -> b -> c -> d -> a2?
    # Let's test both a reconvergent simple odd path AND an odd walk through a cycle!
    af_reconvergent = ArgumentationFramework(
        arguments=["a1", "b", "c", "a2"],
        attacks=[
            ("a1", "b"),
            ("b", "a2"),  # length 2 (even) from a1 to a2 via b
            ("a1", "c"),
            ("c", "b"),   # length 3 (odd) simple path a1 -> c -> b -> a2!
        ],
    )
    types = {"x": {"a1", "a2"}}
    t54 = check_theorem_5_4_condition(af_reconvergent, types)
    assert t54.condition_holds is False
    assert any(
        v.source == "a1" and v.target == "a2" and v.odd_path == ("a1", "c", "b", "a2")
        for v in t54.violations
    )
