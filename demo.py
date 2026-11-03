"""
demo.py

End-to-End Demonstration of:
  1. Part 1: Abstract Argumentation Engine on all Chapter 5 Book Examples
     (Figure 5.1, Figure 5.2, plus odd-cycle / semi-stable vs. preferred / stable showcase).
  2. Part 2: Strategic Argumentation & Grounded Direct Argumentation Mechanism
     on Book Examples 5.10 and 5.11 (including verification of both textbook misprints).
  3. Experiments: 3,000 Random Instances (1,000 per p in {0.15, 0.25, 0.35})
     with 3 agents and 6 to 8 arguments, reporting:
       - Fraction of instances that are strategyproof for each p
       - Instances satisfying Theorem 5.4 yet failing strategyproofness (and why)
       - Instances that are strategyproof although Theorem 5.4's condition fails (and why)
"""

from __future__ import annotations
import argparse
import time

from src.book_examples import format_set, run_book_demonstration
from src.experiments import run_experiments
from src.framework import ArgumentationFramework
from src.labelling import generate_legal_labellings
from src.semantics import compute_all_extensions, report_acceptance_status


def run_additional_semantics_showcase() -> str:
    """
    Demonstrate frameworks where Preferred, Semi-Stable, and Stable extensions
    diverge (e.g., odd-length cycles and asymmetric self-attacking branches).
    """
    lines: list[str] = []
    sep = "=" * 78
    lines.append("\n" + sep)
    lines.append("ADDITIONAL SHOWCASE: PREFERRED vs. SEMI-STABLE vs. STABLE SEMANTICS")
    lines.append(sep)

    # Case A: 3-cycle a1 -> a2 -> a3 -> a1
    odd_cycle = ArgumentationFramework(
        arguments=["a1", "a2", "a3"],
        attacks=[("a1", "a2"), ("a2", "a3"), ("a3", "a1")],
    )
    exts_odd = compute_all_extensions(odd_cycle)
    lines.append("\n[A] Odd 3-Cycle (a1 -> a2 -> a3 -> a1):")
    lines.append(f"    - Grounded   : {[format_set(e) for e in exts_odd['grounded']]}")
    lines.append(f"    - Complete   : {[format_set(e) for e in exts_odd['complete']]}")
    lines.append(f"    - Preferred  : {[format_set(e) for e in exts_odd['preferred']]}")
    lines.append(f"    - Semi-Stable: {[format_set(e) for e in exts_odd['semi_stable']]}")
    lines.append(f"    - Stable     : {[format_set(e) for e in exts_odd['stable']]} (None exists!)")
    lines.append(f"    - Labellings : {generate_legal_labellings(odd_cycle)}")

    # Case B: a1 <-> a2, a2 -> a3, a3 -> a3 (where Preferred = [{a1}, {a2}], Semi-Stable/Stable = [{a2}])
    asymmetric = ArgumentationFramework(
        arguments=["a1", "a2", "a3"],
        attacks=[("a1", "a2"), ("a2", "a1"), ("a2", "a3"), ("a3", "a3")],
    )
    exts_asym = compute_all_extensions(asymmetric)
    lines.append("\n[B] Asymmetric Cycle + Self-Loop (a1 <-> a2, a2 -> a3, a3 -> a3):")
    lines.append(f"    - Grounded   : {[format_set(e) for e in exts_asym['grounded']]}")
    lines.append(f"    - Complete   : {[format_set(e) for e in exts_asym['complete']]}")
    lines.append(f"    - Preferred  : {[format_set(e) for e in exts_asym['preferred']]}")
    lines.append(f"    - Semi-Stable: {[format_set(e) for e in exts_asym['semi_stable']]}")
    lines.append(f"    - Stable     : {[format_set(e) for e in exts_asym['stable']]}")
    for arg in asymmetric.ordered_arguments:
        st_pref = report_acceptance_status(asymmetric, arg, semantics="preferred")
        st_semi = report_acceptance_status(asymmetric, arg, semantics="semi_stable")
        lines.append(
            f"    - Status of {arg}: Preferred='{st_pref}', Semi-Stable='{st_semi}'"
        )

    return "\n".join(lines)


def run_experiments_report(num_instances_per_p: int = 1000, seed: int = 42) -> str:
    """
    Execute the Monte Carlo experiments and format a detailed report answering
    Questions 1, 2, and 3 of the Experiments section.
    """
    t0 = time.perf_counter()
    summaries = run_experiments(
        num_instances_per_p=num_instances_per_p,
        probabilities=(0.15, 0.25, 0.35),
        seed=seed,
    )
    elapsed = time.perf_counter() - t0

    lines: list[str] = []
    sep = "=" * 78
    total_all = sum(s.total_instances for s in summaries.values())

    lines.append("\n" + sep)
    lines.append(
        f"PART 3: MONTE CARLO EXPERIMENTS ({num_instances_per_p} INSTANCES PER p, {total_all} TOTAL)"
    )
    lines.append(sep)
    lines.append(
        f"Configuration: 3 agents, n in {{6, 7, 8}} arguments, p in {{0.15, 0.25, 0.35}}, seed={seed}"
    )
    lines.append(f"Execution Time: {elapsed:.2f} seconds\n")

    header = (
        f"{'p':<6} | {'Instances':<9} | {'Strategyproof (Thm 5.3)':<25} | "
        f"{'Thm 5.4 Holds':<18} | {'Thm5.4 & ~SP':<13} | {'SP & ~Thm5.4':<14}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for p, s in summaries.items():
        sp_str = f"{s.strategyproof_count}/{s.total_instances} ({s.strategyproof_fraction*100:.1f}%)"
        t54_str = f"{s.theorem_5_4_holds_count}/{s.total_instances} ({s.theorem_5_4_holds_fraction*100:.1f}%)"
        lines.append(
            f"{p:<6.2f} | {s.total_instances:<9d} | {sp_str:<25} | "
            f"{t54_str:<18} | {s.t54_holds_but_not_sp_count:<13d} | {s.sp_although_t54_fails_count:<14d}"
        )

    lines.append("\n[Question 1] Fraction of instances that are strategyproof for each p:")
    for p, s in summaries.items():
        lines.append(
            f"  - p = {p:.2f}: {s.strategyproof_fraction:.4f} ({s.strategyproof_count}/{s.total_instances})"
        )

    lines.append(
        "\n[Question 2] Instances that satisfy Theorem 5.4 yet fail strategyproofness:"
    )
    total_q2 = sum(s.t54_holds_but_not_sp_count for s in summaries.values())
    lines.append(f"  - Total across all {total_all} instances: {total_q2}")
    lines.append(
        "  - Explanation: Theorem 5.4 is a mathematically proven SUFFICIENT condition"
    )
    lines.append(
        "    for strategyproofness. If an agent's argument set A_i has no internal"
    )
    lines.append(
        "    (in)direct conflict (no odd-length directed walk/path between any alpha, beta in A_i),"
    )
    lines.append(
        "    revealing an argument alpha in A_i can only attack odd-distance external"
    )
    lines.append(
        "    arguments and defend even-distance arguments, so it can NEVER cause another"
    )
    lines.append(
        "    argument beta in A_i to be rejected from the grounded extension."
    )
    lines.append(
        "    (Note: A naive BFS/DFS that marks vertices visited without tracking edge-length"
    )
    lines.append(
        "    parity or backtracking over cycles would falsely report Theorem 5.4 as holding"
    )
    lines.append(
        "    on reconvergent/cyclic graphs, producing bogus counterexamples.)"
    )

    lines.append(
        "\n[Question 3] Instances that are strategyproof although Theorem 5.4's condition fails:"
    )
    for p, s in summaries.items():
        lines.append(
            f"  - p = {p:.2f}: {s.sp_although_t54_fails_count}/{s.total_instances} instances ({s.sp_although_t54_fails_count/s.total_instances*100:.1f}%)"
        )
        for reason, cnt in sorted(s.reason_breakdown.items(), key=lambda kv: -kv[1]):
            lines.append(f"      * {cnt:4d} instances: {reason}")

    lines.append("\n   Concrete Sample Instances (Strategyproof Despite Theorem 5.4 Failing):")
    for p, s in summaries.items():
        if s.sp_although_t54_fails_examples:
            ex = s.sp_although_t54_fails_examples[0]
            types_str = ", ".join(
                f"{ag}={format_set(args)}" for ag, args in ex.agent_types.items()
            )
            # Prefer showing an indirect odd path between distinct arguments if present
            distinct_viols = [v for v in ex.violations if v.source != v.target]
            indirect_viols = [v for v in distinct_viols if v.length >= 3]
            viol = (
                indirect_viols[0]
                if indirect_viols
                else (distinct_viols[0] if distinct_viols else ex.violations[0])
            )
            lines.append(
                f"  - [p={p:.2f}, Instance #{ex.instance_id}] {ex.af}"
            )
            lines.append(f"      Agent Types : {types_str}")
            lines.append(
                f"      Odd-Path Violation in {viol.agent}: {' -> '.join(viol.odd_path)} (length {viol.length})"
            )
            lines.append(f"      Why Strategyproof : {ex.sp_despite_failure_reason}")

    lines.append("\n  Concrete Sample Instances Where Strategyproofness FAILS (Both Thm 5.3 & 5.4 Fail):")
    for p, s in summaries.items():
        if s.not_sp_examples:
            ex = s.not_sp_examples[0]
            w = ex.witness
            assert w is not None
            types_str = ", ".join(
                f"{ag}={format_set(args)}" for ag, args in ex.agent_types.items()
            )
            others_str = ", ".join(
                f"{ag}={format_set(rep)}" for ag, rep in w.other_agents_reports.items()
            )
            lines.append(
                f"  - [p={p:.2f}, Instance #{ex.instance_id}] {ex.af}"
            )
            lines.append(f"      Agent Types : {types_str}")
            lines.append(
                f"      Manipulator : {w.manipulating_agent} (true type {format_set(w.true_type)}) when others report {others_str}"
            )
            lines.append(
                f"      Truthful    : reveals {format_set(w.true_type)} -> E_grnd={format_set(w.truthful_outcome)} (utility={w.truthful_utility})"
            )
            lines.append(
                f"      Strategic   : reveals {format_set(w.profitable_report)} -> E_grnd={format_set(w.manipulated_outcome)} (utility={w.manipulated_utility})"
            )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstration of Argumentation Engine & Strategic Argumentation."
    )
    parser.add_argument(
        "--instances-per-p",
        type=int,
        default=1000,
        help="Number of random instances to generate per attack probability p (default: 1000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible Monte Carlo experiments (default: 42).",
    )
    args = parser.parse_args()

    print(run_book_demonstration())
    print(run_additional_semantics_showcase())
    print(
        run_experiments_report(
            num_instances_per_p=args.instances_per_p,
            seed=args.seed,
        )
    )


if __name__ == "__main__":
    main()
