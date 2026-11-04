"""
tests/test_experiments_and_examples.py

Unit tests for Component 4: Book Examples demonstration (`src/book_examples.py`),
Random Instance Generator (`allow_self_attacks=True, require_non_empty_agents=True`),
and Verified Outcome Analyzer (`src/experiments.py`).
"""

import random
from src.book_examples import (
    build_example_5_10,
    build_example_5_11,
    build_figure_5_1,
    build_figure_5_2,
    run_book_demonstration,
)
from src.experiments import (
    generate_random_instance,
    run_experiments,
    verify_why_strategyproof_despite_t54_failure,
)
from src.strategic import check_theorem_5_4_condition


def test_book_builders_and_demonstration() -> None:
    f1 = build_figure_5_1()
    assert len(f1.arguments) == 5
    f2 = build_figure_5_2()
    assert len(f2.arguments) == 3

    af10, t10 = build_example_5_10()
    assert len(af10.arguments) == 5
    assert set(t10.keys()) == {"x", "y", "z"}

    af11, t11 = build_example_5_11()
    assert len(af11.arguments) == 6
    assert "a6" in t11["x"]

    output = run_book_demonstration()
    assert "Figure 5.1" in output
    assert "Figure 5.2" in output
    assert "Example 5.10" in output
    assert "Example 5.11" in output
    assert "Misprint" in output


def test_generator_non_empty_and_self_attacks() -> None:
    rng = random.Random(99)
    found_self_attack = False
    for idx in range(50):
        af, types = generate_random_instance(
            rng, p=0.35, instance_id=idx, allow_self_attacks=True, require_non_empty_agents=True
        )
        # Every agent must receive at least 1 argument
        for ag_args in types.values():
            assert len(ag_args) >= 1
        # Partition covers all arguments
        union_args = set().union(*types.values())
        assert union_args == set(af.arguments)
        if any(u == v for u, v in af.attacks):
            found_self_attack = True
    assert found_self_attack is True


def test_verified_explanation_on_example_5_11() -> None:
    af11, t11 = build_example_5_11()
    t54 = check_theorem_5_4_condition(af11, t11)
    assert t54.condition_holds is False
    ver = verify_why_strategyproof_despite_t54_failure(af11, t11, t54.violations)
    assert ver.max_rescued_in_any_profile == 0
    assert "1B. Path Cancelled" in ver.category
    assert ver.truthful_utility == 4


def test_small_experiment_run() -> None:
    summaries = run_experiments(
        num_instances_per_p=30,
        probabilities=(0.15, 0.25, 0.35),
        seed=123,
    )
    for p in (0.15, 0.25, 0.35):
        s = summaries[p]
        assert s.total_instances == 30
        assert 0 <= s.strategyproof_count <= 30
        # Theorem 5.4 is a mathematically sufficient condition:
        # no instance can satisfy Theorem 5.4 yet fail strategyproofness!
        assert s.t54_holds_but_not_sp_count == 0
        assert s.t54_distinct_holds_but_not_sp_count == 0
        assert s.t54_simple_holds_but_not_sp_count == 0
        assert (
            s.theorem_5_4_holds_count
            + s.sp_although_t54_fails_count
            + s.both_fail_count
            == 30
        )
