"""
src/book_examples.py

Reproduces and verifies all examples from Chapter 5 ("Argumentation among Agents"
by Iyad Rahwan in Multiagent Systems, 2nd ed., edited by Gerhard Weiss),
including explicit verification of the two book misprints noted in the assignment.
"""

from __future__ import annotations
from typing import Dict, Set, Tuple

from src.framework import (
    ArgumentationFramework,
    characteristic_function,
    is_conflict_free,
    is_defended_by,
)
from src.labelling import generate_legal_labellings
from src.semantics import (
    check_admissible_and_complete,
    compute_all_extensions,
    compute_complete_extensions,
    compute_grounded_extension,
    report_acceptance_status,
)
from src.strategic import (
    check_theorem_5_3_strategyproof,
    check_theorem_5_4_condition,
    find_best_responses,
    grounded_direct_mechanism,
)


def build_figure_5_1() -> ArgumentationFramework:
    """
    Construct the argumentation framework in Figure 5.1 (Examples 5.5, 5.6, 5.8):
      A = {a1, a2, a3, a4, a5}
      R = {(a3, a2), (a2, a1), (a5, a4), (a4, a1)}
    """
    return ArgumentationFramework(
        arguments=["a1", "a2", "a3", "a4", "a5"],
        attacks=[("a3", "a2"), ("a2", "a1"), ("a5", "a4"), ("a4", "a1")],
    )


def build_figure_5_2() -> ArgumentationFramework:
    """
    Construct the argumentation framework in Figure 5.2 (Examples 5.7, 5.8):
      A = {a1, a2, a3}
      R = {(a1, a2), (a2, a1)}
    """
    return ArgumentationFramework(
        arguments=["a1", "a2", "a3"],
        attacks=[("a1", "a2"), ("a2", "a1")],
    )


def build_example_5_10() -> Tuple[ArgumentationFramework, Dict[str, Set[str]]]:
    """
    Construct the strategic argumentation instance in Example 5.10 (Figure 5.4):
      Agents: x, y, z
      A_x = {a1, a4, a5}, A_y = {a2}, A_z = {a3}
      R = {(a1, a2), (a2, a3), (a3, a4), (a3, a5)}
    """
    af = ArgumentationFramework(
        arguments=["a1", "a2", "a3", "a4", "a5"],
        attacks=[("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")],
    )
    agent_types: Dict[str, Set[str]] = {
        "x": {"a1", "a4", "a5"},
        "y": {"a2"},
        "z": {"a3"},
    }
    return af, agent_types


def build_example_5_11() -> Tuple[ArgumentationFramework, Dict[str, Set[str]]]:
    """
    Construct the strategic argumentation instance in Example 5.11 (Figure 5.5):
      Variant of Example 5.10 with additional argument a6 in A_x and attack (a6, a3).
      Agents: x, y, z
      A_x = {a1, a4, a5, a6}, A_y = {a2}, A_z = {a3}
      R = {(a1, a2), (a2, a3), (a3, a4), (a3, a5), (a6, a3)}
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
    agent_types: Dict[str, Set[str]] = {
        "x": {"a1", "a4", "a5", "a6"},
        "y": {"a2"},
        "z": {"a3"},
    }
    return af, agent_types


def format_set(s: Set[str] | frozenset[str]) -> str:
    """Format a set of arguments in sorted order, e.g. '{a1, a3}' or 'empty'."""
    if not s:
        return "empty"
    return "{" + ", ".join(sorted(s)) + "}"


def run_book_demonstration() -> str:
    """
    Execute all book examples from Chapter 5 and return a formatted report string.
    """
    lines: list[str] = []
    sep = "=" * 78

    lines.append(sep)
    lines.append("PART 1: ABSTRACT ARGUMENTATION ENGINE — BOOK EXAMPLES (CHAPTER 5)")
    lines.append(sep)

    # -------------------------------------------------------------------------
    # 1. Figure 5.1 (Examples 5.5, 5.6, 5.8)
    # -------------------------------------------------------------------------
    af_5_1 = build_figure_5_1()
    lines.append("\n[1] Figure 5.1 (Examples 5.5, 5.6, 5.8)")
    lines.append(f"    Framework: {af_5_1}")
    lines.append(
        f"    - Conflict-free test on {{a3, a5}}: {is_conflict_free(af_5_1, {'a3', 'a5'})}"
    )
    lines.append(
        f"    - Conflict-free test on {{a1, a2}}: {is_conflict_free(af_5_1, {'a1', 'a2'})}"
    )
    lines.append(
        f"    - Defense test: Does {{a3, a5}} defend a1? {is_defended_by(af_5_1, 'a1', {'a3', 'a5'})}"
    )
    lines.append(
        f"    - Defense test: Does {{a3}} alone defend a1? {is_defended_by(af_5_1, 'a1', {'a3'})}"
    )
    lines.append("    - Characteristic function F_AF(S) iterations (Example 5.6):")
    lines.append(f"        F(empty)          = {format_set(characteristic_function(af_5_1, set()))}")
    lines.append(f"        F({{a3}})           = {format_set(characteristic_function(af_5_1, {'a3'}))}")
    lines.append(f"        F({{a3, a5}})       = {format_set(characteristic_function(af_5_1, {'a3', 'a5'}))}")
    lines.append(
        f"        F({{a1, a3, a5}})   = {format_set(characteristic_function(af_5_1, {'a1', 'a3', 'a5'}))}"
    )

    lines.append("    - Admissibility & Completeness checks (Examples 5.5 & 5.6):")
    for test_s in [set(), {"a3"}, {"a5"}, {"a3", "a5"}, {"a1", "a3", "a5"}, {"a1"}]:
        chk = check_admissible_and_complete(af_5_1, test_s)
        lines.append(
            f"        S = {format_set(test_s):<14} -> admissible={chk['is_admissible']}, complete={chk['is_complete']}"
        )

    exts_5_1 = compute_all_extensions(af_5_1)
    lines.append(f"    - Grounded Extension  : {format_set(compute_grounded_extension(af_5_1))}")
    lines.append(
        f"    - Complete Extensions : {[format_set(e) for e in exts_5_1['complete']]}"
    )
    lines.append(
        f"    - Preferred Extensions: {[format_set(e) for e in exts_5_1['preferred']]}"
    )
    lines.append(
        f"    - Stable Extensions   : {[format_set(e) for e in exts_5_1['stable']]}"
    )
    lines.append(
        f"    - Semi-Stable Exts    : {[format_set(e) for e in exts_5_1['semi_stable']]}"
    )
    lines.append(f"    - Legal Labellings    : {generate_legal_labellings(af_5_1)}")
    lines.append("    - Argument Acceptance Status (Definition 5.8):")
    for arg in af_5_1.ordered_arguments:
        lines.append(
            f"        {arg}: {report_acceptance_status(af_5_1, arg, semantics='preferred')}"
        )

    # -------------------------------------------------------------------------
    # 2. Figure 5.2 (Examples 5.7, 5.8)
    # -------------------------------------------------------------------------
    af_5_2 = build_figure_5_2()
    lines.append("\n[2] Figure 5.2 (Examples 5.7 & 5.8 — Multiple Extensions & Labellings)")
    lines.append(f"    Framework: {af_5_2}")
    exts_5_2 = compute_all_extensions(af_5_2)
    lines.append(f"    - Grounded Extension  : {format_set(compute_grounded_extension(af_5_2))}")
    lines.append(
        f"    - Complete Extensions : {[format_set(e) for e in compute_complete_extensions(af_5_2)]}"
    )
    lines.append(
        f"    - Preferred Extensions: {[format_set(e) for e in exts_5_2['preferred']]}"
    )
    lines.append(
        f"    - Stable Extensions   : {[format_set(e) for e in exts_5_2['stable']]}"
    )
    lines.append(
        f"    - Semi-Stable Exts    : {[format_set(e) for e in exts_5_2['semi_stable']]}"
    )
    lines.append("    - Legal (in/out/undec) Labellings (Figure 5.2: L_G, L_1, L_2):")
    for idx, lbl in enumerate(generate_legal_labellings(af_5_2)):
        tag = "L_G" if idx == 0 else f"L_{idx}"
        lines.append(f"        {tag}: {lbl}")
    lines.append("    - Argument Acceptance Status (under Preferred/Complete semantics):")
    for arg in af_5_2.ordered_arguments:
        lines.append(
            f"        {arg}: {report_acceptance_status(af_5_2, arg, semantics='preferred')}"
        )

    # -------------------------------------------------------------------------
    # 3. Example 5.10 & Example 5.11 (Strategic Argumentation)
    # -------------------------------------------------------------------------
    lines.append("\n" + sep)
    lines.append("PART 2: STRATEGIC ARGUMENTATION — BOOK EXAMPLES 5.10 & 5.11")
    lines.append(sep)

    af_5_10, types_5_10 = build_example_5_10()
    lines.append("\n[3] Example 5.10 (Hiding Arguments is Beneficial)")
    lines.append(f"    Framework: {af_5_10}")
    lines.append(
        f"    Agent Types: A_x={format_set(types_5_10['x'])}, A_y={format_set(types_5_10['y'])}, A_z={format_set(types_5_10['z'])}"
    )
    o_5_10 = grounded_direct_mechanism(af_5_10, types_5_10)
    u_x = len(types_5_10["x"] & o_5_10)
    u_y = len(types_5_10["y"] & o_5_10)
    u_z = len(types_5_10["z"] & o_5_10)
    lines.append(f"    - Truthful Outcome E_grnd(A) = {format_set(o_5_10)}")
    lines.append(
        f"    - True Utilities under Truthfulness: u_x={u_x}, u_y={u_y}, u_z={u_z}"
    )
    lines.append(
        "      [Book Misprint #1 Note: The textbook writes u_y(o,{a3})=1 and u_z(o,{a2})=0,"
    )
    lines.append(
        "       swapping y's and z's argument sets! Correctly, A_y={a2} gives u_y=0 and A_z={a3} gives u_z=1.]"
    )

    br_x_5_10 = find_best_responses(
        af_5_10, "x", types_5_10["x"], {"y": types_5_10["y"], "z": types_5_10["z"]}
    )
    lines.append("    - Enumerating all subsets of A_x given A_y={a2}, A_z={a3}:")
    for rep, util, out_ext in br_x_5_10.utility_by_report:
        lines.append(
            f"        Reveal {format_set(rep):<14} -> Induced E_grnd = {format_set(out_ext):<14} -> u_x = {util}"
        )
    lines.append(
        f"    - Best Responses for Agent x: {[format_set(r) for r in br_x_5_10.best_reports]} (max utility = {br_x_5_10.max_utility} > truthful utility = {br_x_5_10.truthful_utility})"
    )

    t53_5_10 = check_theorem_5_3_strategyproof(af_5_10, types_5_10)
    t54_5_10 = check_theorem_5_4_condition(af_5_10, types_5_10)
    lines.append(f"    - Theorem 5.3 Strategyproof? {t53_5_10.is_strategyproof}")
    lines.append(
        f"    - Theorem 5.4 Condition Holds? {t54_5_10.condition_holds} (Violations: {[('->'.join(v.odd_path)) for v in t54_5_10.violations]})"
    )

    # Example 5.11
    af_5_11, types_5_11 = build_example_5_11()
    lines.append("\n[4] Example 5.11 (Truthfulness Despite Indirect Self-Defeat)")
    lines.append(f"    Framework: {af_5_11}")
    lines.append(
        f"    Agent Types: A_x={format_set(types_5_11['x'])}, A_y={format_set(types_5_11['y'])}, A_z={format_set(types_5_11['z'])}"
    )
    o_5_11 = grounded_direct_mechanism(af_5_11, types_5_11)
    lines.append(f"    - Truthful Outcome E_grnd(A) = {format_set(o_5_11)} (u_x = {len(types_5_11['x'] & o_5_11)})")
    t53_5_11 = check_theorem_5_3_strategyproof(af_5_11, types_5_11)
    t54_5_11 = check_theorem_5_4_condition(af_5_11, types_5_11)
    lines.append(f"    - Theorem 5.3 Strategyproof? {t53_5_11.is_strategyproof}")
    lines.append(
        f"    - Theorem 5.4 Condition Holds? {t54_5_11.condition_holds} (Violations: {[('->'.join(v.odd_path)) for v in t54_5_11.violations]})"
    )
    lines.append(
        "      [Book Misprint #2 Note: In the discussion after Example 5.11, the argument that"
    )
    lines.append(
        "       cancels the indirect self-defeat (a1->a2->a3->a4 and a1->a2->a3->a5) by directly"
    )
    lines.append(
        "       defeating a3 is a6 (via a6->a3), NOT a5 as misprinted in the book!]"
    )

    return "\n".join(lines)
