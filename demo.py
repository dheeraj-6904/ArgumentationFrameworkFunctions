"""
demo.py

End-to-End Demonstration of:
  1. Part 1: Abstract Argumentation Engine on all Chapter 5 Book Examples
     (Figure 5.1, Figure 5.2, plus odd-cycle / semi-stable vs. preferred / stable showcase).
  2. Part 2: Strategic Argumentation & Grounded Direct Argumentation Mechanism
     on Book Examples 5.10 and 5.11 (including verification of both textbook misprints
     and a concrete cyclic/reconvergent graph demonstrating why naive visited-set BFS
     fails on Theorem 5.4).
  3. Part 3: Monte Carlo Experiments on 3,000 Random Instances (1,000 per p in {0.15, 0.25, 0.35})
     with 3 non-empty agents, 6 to 8 arguments, and all n^2 possible directed attacks
     (including self-attacks), plus a sensitivity comparison across generator variants.
"""

from __future__ import annotations
import argparse
import time

from src.book_examples import format_set, run_book_demonstration
from src.experiments import run_experiments
from src.framework import ArgumentationFramework
from src.labelling import generate_legal_labellings
from src.semantics import compute_all_extensions, report_acceptance_status
from src.strategic import (
    check_theorem_5_3_strategyproof,
    check_theorem_5_4_condition,
    has_odd_path_naive_visited,
)


def run_additional_semantics_showcase() -> str:
    """
    Demonstrate frameworks where Preferred, Semi-Stable, and Stable extensions
    diverge, and demonstrate why cycle-aware parity search is required for Theorem 5.4.
    """
    lines: list[str] = []
    sep = "=" * 78
    lines.append("\n" + sep)
    lines.append("ADDITIONAL SHOWCASE: SEMANTICS DIVERGENCE & CYCLE-AWARE THEOREM 5.4")
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

    # Case B: a1 <-> a2, a2 -> a3, a3 -> a3 (Preferred = [{a1}, {a2}], Semi-Stable/Stable = [{a2}])
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

    # Case C: Reconvergent/Cyclic Graph Where Naive Visited-Set BFS Fails on Theorem 5.4
    af_cyc = ArgumentationFramework(
        arguments=["a1", "a2", "a3", "a4", "a5", "b1", "b2", "c"],
        attacks=[
            ("a1", "c"),
            ("c", "a2"),
            ("a2", "c"),   # 2-cycle c <-> a2
            ("a1", "b1"),
            ("b1", "b2"),
            ("b2", "a2"),
            ("a2", "a3"),
            ("a3", "a4"),
            ("a3", "a5"),
        ],
    )
    types_cyc = {
        "x": {"a1", "a4", "a5"},
        "y": {"b1", "a2"},
        "z": {"b2", "c", "a3"},
    }
    naive_any_odd = any(
        has_odd_path_naive_visited(af_cyc, u, v)
        for args in types_cyc.values()
        for u in args
        for v in args
    )
    t53_cyc = check_theorem_5_3_strategyproof(af_cyc, types_cyc)
    t54_cyc = check_theorem_5_4_condition(af_cyc, types_cyc)
    lines.append(
        "\n[C] Cyclic/Reconvergent Graph Demonstrating Why Cycle-Aware Parity Search is Essential:"
    )
    lines.append(f"    Framework  : {af_cyc}")
    lines.append("    Agent Types: A_x={a1, a4, a5}, A_y={b1, a2}, A_z={b2, c, a3}")
    lines.append(
        "    - Even path from a1 to a4/a5 (length 4): a1 -> c -> a2 -> a3 -> a4 (visits a2 at even dist 2)"
    )
    lines.append(
        "    - Odd path  from a1 to a4/a5 (length 5): a1 -> b1 -> b2 -> a2 -> a3 -> a4 (reaches a2 at odd dist 3)"
    )
    lines.append(
        f"    - Naive Single-Visited-Set BFS (`has_odd_path_naive_visited`): finds odd path? {naive_any_odd} (FALSE POSITIVE: claims Thm 5.4 holds!)"
    )
    lines.append(
        f"    - Cycle-Aware Theorem 5.4 Checker (`check_theorem_5_4_condition`): holds? {t54_cyc.condition_holds} "
        f"(catches {[('->'.join(v.odd_path)) for v in t54_cyc.violations]})"
    )
    lines.append(
        f"    - Exact Strategyproofness (`check_theorem_5_3_strategyproof`): {t53_cyc.is_strategyproof} "
        f"(Agent x gains utility 2 > 1 by hiding a1 when Agent y reveals {{b1, a2}} and Agent z reveals {{b2, a3}})"
    )

    return "\n".join(lines)


def run_experiments_report(num_instances_per_p: int = 1000, seed: int = 42) -> str:
    """
    Execute the Monte Carlo experiments and format a detailed report answering
    Questions 1, 2, and 3 of the Experiments section, plus a generator sensitivity
    comparison table.
    """
    t0 = time.perf_counter()
    summaries = run_experiments(
        num_instances_per_p=num_instances_per_p,
        probabilities=(0.15, 0.25, 0.35),
        seed=seed,
        allow_self_attacks=True,
        require_non_empty_agents=True,
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
        f"Primary Generator Settings: 3 non-empty agents, n in {{6, 7, 8}} arguments, "
        f"all n^2 directed attacks (self-attacks included) sampled with probability p in {{0.15, 0.25, 0.35}}, seed={seed}"
    )
    lines.append(f"Execution Time: {elapsed:.2f} seconds\n")

    header = (
        f"{'p':<5} | {'N':<5} | {'Strategyproof (Thm 5.3)':<23} | "
        f"{'Thm5.4 (All Pairs)':<18} | {'Thm5.4 (Distinct)':<17} | "
        f"{'Thm5.4 & ~SP':<12} | {'SP & ~Thm5.4':<12}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for p, s in summaries.items():
        sp_str = f"{s.strategyproof_count}/{s.total_instances} ({s.strategyproof_fraction*100:.1f}%)"
        t54_all_str = f"{s.theorem_5_4_holds_count}/{s.total_instances} ({s.theorem_5_4_holds_fraction*100:.1f}%)"
        t54_dist_str = (
            f"{s.theorem_5_4_distinct_holds_count}/{s.total_instances} "
            f"({s.theorem_5_4_distinct_holds_count/s.total_instances*100:.1f}%)"
        )
        lines.append(
            f"{p:<5.2f} | {s.total_instances:<5d} | {sp_str:<23} | "
            f"{t54_all_str:<18} | {t54_dist_str:<17} | "
            f"{s.t54_holds_but_not_sp_count:<12d} | {s.sp_although_t54_fails_count:<12d}"
        )

    lines.append("\n[Question 1] Fraction of instances that are strategyproof for each p:")
    for p, s in summaries.items():
        lines.append(
            f"  - p = {p:.2f}: {s.strategyproof_fraction:.4f} ({s.strategyproof_count}/{s.total_instances})"
        )

    lines.append(
        "\n[Question 2] Instances that satisfy Theorem 5.4 yet fail strategyproofness:"
    )
    total_q2_all = sum(s.t54_holds_but_not_sp_count for s in summaries.values())
    total_q2_dist = sum(s.t54_distinct_holds_but_not_sp_count for s in summaries.values())
    total_q2_simp = sum(s.t54_simple_holds_but_not_sp_count for s in summaries.values())
    lines.append(
        f"  - Under Theorem 5.4 (all pairs alpha, beta in A_i, walks allowed)     : {total_q2_all}/{total_all}"
    )
    lines.append(
        f"  - Under Theorem 5.4 (distinct pairs alpha != beta, walks allowed)     : {total_q2_dist}/{total_all}"
    )
    lines.append(
        f"  - Under Theorem 5.4 (simple odd paths only, no repeated cycle nodes)  : {total_q2_simp}/{total_all}"
    )
    lines.append("  - Diagnostic — Non-strategyproof instances with ONLY length-1 odd paths (no odd path of length >= 3):")
    for p, s in summaries.items():
        lines.append(
            f"      * p = {p:.2f}: {s.only_len_1_not_sp_count} instances (if a checker ignored length-1 conflicts and only tested length >= 3, these would be false positives)"
        )

    lines.append(
        "\n[Question 3] Instances that are strategyproof although Theorem 5.4's condition fails:"
    )
    lines.append(
        "  (Verified by exhaustively computing G(S) = (A_i cap E_dev) \\ E_truth [rescued arguments]"
    )
    lines.append(
        "   and L(S) = (A_i cap E_truth) \\ E_dev [sacrificed arguments] across ALL opponent profiles and ALL subsets S subseteq A_i)"
    )
    for p, s in summaries.items():
        lines.append(
            f"  - p = {p:.2f}: {s.sp_although_t54_fails_count}/{s.total_instances} instances ({s.sp_although_t54_fails_count/s.total_instances*100:.1f}%)"
        )
        for reason, cnt in sorted(s.reason_breakdown.items(), key=lambda kv: kv[0]):
            lines.append(f"      * {cnt:4d} instances: {reason}")

    lines.append(
        "\n  Concrete Sample Instances & Full Deviation Verification (Strategyproof Despite Theorem 5.4 Failing):"
    )
    for p, s in summaries.items():
        if s.sp_although_t54_fails_examples:
            ex = s.sp_although_t54_fails_examples[0]
            v_exp = ex.verified_explanation
            assert v_exp is not None
            viol = v_exp.focus_violation
            path_kind = (
                "Simple odd path (no repeated vertices)"
                if viol.is_simple_path
                else "Odd directed walk (traverses cycle; repeated vertices allowed)"
            )
            types_str = ", ".join(
                f"{ag}={format_set(args)}" for ag, args in ex.agent_types.items()
            )
            others_str = ", ".join(
                f"{ag}={format_set(rep)}"
                for ag, rep in v_exp.witness_opponent_reports.items()
            )
            lines.append(
                f"\n  - [p={p:.2f}, Instance #{ex.instance_id}] {ex.af}"
            )
            lines.append(f"      Agent Types        : {types_str}")
            lines.append(
                f"      Focus Violation    : {viol.agent} holds ({viol.source}, {viol.target}) with {' -> '.join(viol.odd_path)} "
                f"[length {viol.length}, {path_kind}]"
            )
            lines.append(f"      Verified Category  : {v_exp.category}")
            lines.append(
                f"      Max Rescued |G(S)| : {v_exp.max_rescued_in_any_profile} across all opponent report profiles"
            )
            lines.append(
                f"      Deviation Table for {v_exp.focus_agent} (against opponent reports {others_str}):"
            )
            for row in v_exp.deviation_table:
                lines.append(
                    f"        Reveal S={format_set(row.revealed_subset):<14} -> "
                    f"E_dev={format_set(row.induced_grounded):<18} | "
                    f"Own Accepted={format_set(row.accepted_own):<14} | "
                    f"Rescued G={format_set(row.rescued_args):<10} | "
                    f"Sacrificed L={format_set(row.sacrificed_args):<10} | "
                    f"u={row.utility}"
                )

    lines.append(
        "\n  Concrete Sample Instances Where Strategyproofness FAILS (Both Thm 5.3 & 5.4 Fail):"
    )
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

    # -------------------------------------------------------------------------
    # Generator & Design-Choice Sensitivity Table
    # -------------------------------------------------------------------------
    lines.append("\n" + sep)
    lines.append("APPENDIX: GENERATOR & DESIGN-CHOICE SENSITIVITY COMPARISON (SEED=42)")
    lines.append(sep)
    configs = [
        (True, True, "n^2 attacks (self-attacks ON),  Non-Empty Agents (PRIMARY)"),
        (True, False, "n^2 attacks (self-attacks ON),  Unrestricted i.i.d. Agents"),
        (False, True, "n(n-1) attacks (no self-loops), Non-Empty Agents"),
        (False, False, "n(n-1) attacks (no self-loops), Unrestricted i.i.d. Agents"),
    ]
    for self_att, non_emp, label in configs:
        sub_sum = run_experiments(
            num_instances_per_p=num_instances_per_p,
            probabilities=(0.15, 0.25, 0.35),
            seed=seed,
            allow_self_attacks=self_att,
            require_non_empty_agents=non_emp,
        )
        sp_list = [f"p={p}: {sub_sum[p].strategyproof_count}/{num_instances_per_p}" for p in (0.15, 0.25, 0.35)]
        t54_all_list = [f"p={p}: {sub_sum[p].theorem_5_4_holds_count}" for p in (0.15, 0.25, 0.35)]
        t54_dist_list = [f"p={p}: {sub_sum[p].theorem_5_4_distinct_holds_count}" for p in (0.15, 0.25, 0.35)]
        q2_list = [sub_sum[p].t54_holds_but_not_sp_count for p in (0.15, 0.25, 0.35)]
        lines.append(f"\n  * {label}:")
        lines.append(f"      Strategyproof (Thm 5.3)      : {', '.join(sp_list)}")
        lines.append(f"      Thm 5.4 Holds (All Pairs)    : {', '.join(t54_all_list)}")
        lines.append(f"      Thm 5.4 Holds (Distinct Only): {', '.join(t54_dist_list)}")
        lines.append(f"      Thm 5.4 Holds & ~SP (Q2)     : {q2_list} (Always 0!)")

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
