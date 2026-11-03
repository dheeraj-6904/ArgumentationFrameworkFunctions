"""
tests/test_experiments_and_examples.py

Unit tests for Component 4: Book Examples demonstration (`src/book_examples.py`)
and Random Instance Experiments (`src/experiments.py`).
"""

from src.book_examples import (
    build_example_5_10,
    build_example_5_11,
    build_figure_5_1,
    build_figure_5_2,
    run_book_demonstration,
)
from src.experiments import run_experiments


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
        assert (
            s.theorem_5_4_holds_count
            + s.sp_although_t54_fails_count
            + s.both_fail_count
            == 30
        )
