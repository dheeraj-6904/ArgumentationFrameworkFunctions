"""
src/semantics.py

Extension-based semantics and argument acceptance status for Abstract
Argumentation Frameworks (Part 1: Items 5, 6A, 6B, 6C, 6E).

Design Principles (SOLID):
- Single Responsibility: Extension computation and acceptance status evaluation.
- Open/Closed & Liskov Substitution: Defines `SemanticsEvaluator` abstract base
  class with interchangeable concrete implementations (`GroundedSemantics`,
  `CompleteSemantics`, `PreferredSemantics`, `StableSemantics`, `SemiStableSemantics`).
- Interface Segregation: Exposes clean standalone functions matching each item
  in the assignment specification.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, FrozenSet, Iterable, List, Set

from src.framework import (
    ArgumentationFramework,
    characteristic_function,
    is_conflict_free,
)


# ============================================================================
# Item 5: Admissibility and Complete Extension Checks
# ============================================================================


def is_admissible(af: ArgumentationFramework, S: Iterable[str]) -> bool:
    """
    Check if a given set S of arguments is admissible.

    Definition (Dung 1995 / Rahwan Ch. 5, Def. 5.4):
    A set of arguments S subseteq A is admissible iff:
      1. S is conflict-free, and
      2. S defends every argument in S (i.e., S subseteq F_AF(S)).
    """
    s_set = af._validate_subset(S)
    if not is_conflict_free(af, s_set):
        return False

    # Check if every alpha in S has all its attackers defeated by S
    s_plus = af.set_attacked_by(s_set)
    for alpha in s_set:
        if not af.attackers_of(alpha).issubset(s_plus):
            return False
    return True


def is_complete_extension(af: ArgumentationFramework, S: Iterable[str]) -> bool:
    """
    Check if a given set S of arguments is a complete extension.

    Definition (Dung 1995 / Rahwan Ch. 5, Def. 5.6):
    A set S subseteq A is a complete extension iff:
      1. S is admissible (conflict-free and self-defending), and
      2. Every argument defended by S is contained in S.
    Equivalently, S is conflict-free and is a fixed point of F_AF: S == F_AF(S).
    """
    s_set = af._validate_subset(S)
    if not is_conflict_free(af, s_set):
        return False
    return characteristic_function(af, s_set) == s_set


def check_admissible_and_complete(
    af: ArgumentationFramework, S: Iterable[str]
) -> Dict[str, bool]:
    """
    Item 5: Check if a given set S is admissible and is a complete extension.
    Returns a dictionary with both boolean evaluations:
        {"is_admissible": bool, "is_complete": bool}
    """
    s_set = af._validate_subset(S)
    if not is_conflict_free(af, s_set):
        return {"is_admissible": False, "is_complete": False}

    defended = characteristic_function(af, s_set)
    admissible = s_set.issubset(defended)
    complete = admissible and (s_set == defended)
    return {"is_admissible": admissible, "is_complete": complete}


# ============================================================================
# SOLID Strategy / Evaluator Hierarchy for Argumentation Semantics
# ============================================================================


class SemanticsEvaluator(ABC):
    """
    Abstract base class (Open/Closed & Liskov Substitution Principles) for all
    extension-based argumentation semantics evaluators.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier name of the semantics."""

    @abstractmethod
    def compute_extensions(self, af: ArgumentationFramework) -> List[Set[str]]:
        """Compute all extensions of `af` under this semantics."""


class GroundedSemantics(SemanticsEvaluator):
    """
    Computes the unique Grounded Extension (least fixed point of F_AF).
    """

    @property
    def name(self) -> str:
        return "grounded"

    def compute_extensions(self, af: ArgumentationFramework) -> List[Set[str]]:
        return [compute_grounded_extension(af)]


class CompleteSemantics(SemanticsEvaluator):
    """
    Computes all Complete Extensions (conflict-free fixed points S == F_AF(S)).
    """

    @property
    def name(self) -> str:
        return "complete"

    def compute_extensions(self, af: ArgumentationFramework) -> List[Set[str]]:
        return compute_complete_extensions(af)


class PreferredSemantics(SemanticsEvaluator):
    """
    Computes all Preferred Extensions (maximal complete/admissible extensions w.r.t. subseteq).
    """

    @property
    def name(self) -> str:
        return "preferred"

    def compute_extensions(self, af: ArgumentationFramework) -> List[Set[str]]:
        return compute_preferred_extensions(af)


class StableSemantics(SemanticsEvaluator):
    """
    Computes all Stable Extensions (conflict-free sets S where S cup S^+ == A).
    """

    @property
    def name(self) -> str:
        return "stable"

    def compute_extensions(self, af: ArgumentationFramework) -> List[Set[str]]:
        return compute_stable_extensions(af)


class SemiStableSemantics(SemanticsEvaluator):
    """
    Computes all Semi-Stable Extensions (complete extensions S where range S cup S^+
    is maximal w.r.t. subseteq).
    """

    @property
    def name(self) -> str:
        return "semi_stable"

    def compute_extensions(self, af: ArgumentationFramework) -> List[Set[str]]:
        return compute_semi_stable_extensions(af)


# ============================================================================
# Item 6 (A), (B), (C), (E): Standalone Extension & Status Functions
# ============================================================================


def compute_grounded_extension(af: ArgumentationFramework) -> Set[str]:
    """
    Item 6(A): Compute the grounded extension of a given argumentation framework.

    Algorithm (Least Fixed Point of Characteristic Function F_AF):
    Since F_AF is monotonic on the finite power-set lattice (2^A, subseteq),
    Tarski's Fixed Point Theorem guarantees that iterating:
        S_0 = empty set
        S_{k+1} = F_AF(S_k)
    converges to the unique minimal complete extension in at most |A| iterations.
    """
    current: Set[str] = set()
    while True:
        next_set = characteristic_function(af, current)
        if next_set == current:
            return current
        current = next_set


def compute_complete_extensions(af: ArgumentationFramework) -> List[Set[str]]:
    """
    Item 6(B): Compute all complete extensions of a given argumentation framework.

    Algorithm (Pruned Backtracking Search seeded with the Grounded Extension):
    1. Every complete extension E is a superset of the grounded extension E_grnd.
    2. Furthermore, since E is conflict-free and contains E_grnd, E cannot contain
       any argument attacked by E_grnd (E_grnd^+) nor any argument that attacks E_grnd,
       nor any self-attacking argument.
    3. We therefore restrict candidate expansion arguments to:
           candidates = { a in A \\ (E_grnd cup E_grnd^+) | not (a -> a) }
    4. We perform recursive depth-first backtracking to enumerate conflict-free
       subsets of `candidates`, pruning branches immediately whenever an argument
       conflicts with already-selected arguments, and collect all S where F_AF(S) == S.
    """
    grounded = compute_grounded_extension(af)
    grounded_plus = af.set_attacked_by(grounded)

    # Candidate arguments outside (grounded cup grounded^+) without self-loops
    candidates: List[str] = [
        arg
        for arg in af.ordered_arguments
        if arg not in grounded
        and arg not in grounded_plus
        and arg not in af.attacked_by(arg)
    ]

    complete_exts: List[Set[str]] = []

    def backtrack(idx: int, current_set: Set[str], forbidden: Set[str]) -> None:
        # When all candidates have been considered, check the fixed-point condition
        if idx == len(candidates):
            if characteristic_function(af, current_set) == current_set:
                complete_exts.append(set(current_set))
            return

        arg = candidates[idx]

        # Branch 1: Exclude `arg`
        backtrack(idx + 1, current_set, forbidden)

        # Branch 2: Include `arg` (only if `arg` does not conflict with `current_set`)
        if arg not in forbidden:
            current_set.add(arg)
            # Any argument attacked by `arg` or attacking `arg` cannot be added later
            new_forbidden = (
                forbidden
                | set(af.attacked_by(arg))
                | set(af.attackers_of(arg))
            )
            backtrack(idx + 1, current_set, new_forbidden)
            current_set.remove(arg)

    # Initialize forbidden set with anything that attacks or is attacked by `grounded`
    initial_forbidden: Set[str] = set(grounded_plus)
    for g_arg in grounded:
        initial_forbidden.update(af.attackers_of(g_arg))

    backtrack(0, set(grounded), initial_forbidden)

    # Sort deterministically by size then lexicographically
    complete_exts.sort(key=lambda s: (len(s), sorted(s)))
    return complete_exts


def _filter_maximal_sets(sets: List[Set[str]]) -> List[Set[str]]:
    """
    Helper: Return all sets in `sets` that are maximal w.r.t. set inclusion (subseteq).
    """
    maximal: List[Set[str]] = []
    for i, s_i in enumerate(sets):
        is_strictly_contained = False
        for j, s_j in enumerate(sets):
            if i != j and s_i < s_j:  # strict subset test
                is_strictly_contained = True
                break
        if not is_strictly_contained:
            maximal.append(set(s_i))
    return maximal


def compute_preferred_extensions(
    af: ArgumentationFramework,
    complete_exts: List[Set[str]] | None = None,
) -> List[Set[str]]:
    """
    Compute all preferred extensions (maximal complete/admissible extensions w.r.t. subseteq).
    """
    if complete_exts is None:
        complete_exts = compute_complete_extensions(af)
    return _filter_maximal_sets(complete_exts)


def compute_stable_extensions(
    af: ArgumentationFramework,
    complete_exts: List[Set[str]] | None = None,
) -> List[Set[str]]:
    """
    Compute all stable extensions: conflict-free sets S (which are necessarily
    complete extensions) that attack every argument outside S (i.e., S cup S^+ == A).
    """
    if complete_exts is None:
        complete_exts = compute_complete_extensions(af)
    all_args = af.arguments
    stable: List[Set[str]] = []
    for ext in complete_exts:
        ext_plus = af.set_attacked_by(ext)
        if (ext | ext_plus) == all_args:
            stable.append(set(ext))
    return stable


def compute_semi_stable_extensions(
    af: ArgumentationFramework,
    complete_exts: List[Set[str]] | None = None,
) -> List[Set[str]]:
    """
    Compute all semi-stable extensions: complete extensions S for which the
    range (S cup S^+) is maximal w.r.t. set inclusion among all complete extensions.
    """
    if complete_exts is None:
        complete_exts = compute_complete_extensions(af)

    # Compute the range R(E) = E cup E^+ for each complete extension E
    ranges: List[FrozenSet[str]] = [
        frozenset(ext | af.set_attacked_by(ext)) for ext in complete_exts
    ]

    semi_stable: List[Set[str]] = []
    for i, ext in enumerate(complete_exts):
        r_i = ranges[i]
        # Check if any other complete extension has a strictly larger range
        if not any(r_i < r_j for j, r_j in enumerate(ranges) if i != j):
            semi_stable.append(set(ext))
    return semi_stable


def compute_all_extensions(
    af: ArgumentationFramework,
) -> Dict[str, List[Set[str]]]:
    """
    Item 6(C): Compute a list of all extensions (preferred, stable, and semi-stable),
    as well as grounded and complete extensions for convenience.

    Returns a dictionary mapping semantics name to its list of extensions:
        {
            "grounded": [grounded_ext],
            "complete": [...],
            "preferred": [...],
            "stable": [...],
            "semi_stable": [...],
        }
    """
    complete = compute_complete_extensions(af)
    grounded = compute_grounded_extension(af)
    preferred = compute_preferred_extensions(af, complete_exts=complete)
    stable = compute_stable_extensions(af, complete_exts=complete)
    semi_stable = compute_semi_stable_extensions(af, complete_exts=complete)
    return {
        "grounded": [grounded],
        "complete": complete,
        "preferred": preferred,
        "stable": stable,
        "semi_stable": semi_stable,
    }


def report_acceptance_status(
    af: ArgumentationFramework,
    alpha: str,
    semantics: str = "preferred",
) -> str:
    """
    Item 6(E): Report the acceptance status of a given argument alpha:
      - "skeptically accepted": alpha belongs to ALL extensions under the semantics
      - "credulously accepted": alpha belongs to AT LEAST ONE (but not all) extensions
      - "rejected": alpha belongs to NO extensions under the semantics

    Note on Definition 5.8 (Rahwan Ch. 5):
      1. alpha is skeptically accepted iff alpha in E_i for all i = 1..n.
      2. alpha is credulously accepted iff exists E_i such that alpha in E_i.
      3. alpha is rejected iff alpha not in E_i for all i = 1..n.
    (Any skeptically accepted argument is also credulously accepted by Definition 5.8;
    as a mutually exclusive status label, "skeptically accepted" is the strongest
    acceptance level, followed by "credulously accepted", then "rejected".)
    """
    if alpha not in af.arguments:
        raise ValueError(f"Argument '{alpha}' is not in the argumentation framework.")

    evaluators: Dict[str, SemanticsEvaluator] = {
        "grounded": GroundedSemantics(),
        "complete": CompleteSemantics(),
        "preferred": PreferredSemantics(),
        "stable": StableSemantics(),
        "semi_stable": SemiStableSemantics(),
    }
    sem_key = semantics.lower().replace("-", "_")
    if sem_key not in evaluators:
        raise ValueError(
            f"Unknown semantics '{semantics}'. Choose from {sorted(evaluators.keys())}."
        )

    extensions = evaluators[sem_key].compute_extensions(af)
    if not extensions:
        # e.g., stable semantics on an odd-length cycle where no extension exists
        return "rejected"

    in_all = all(alpha in ext for ext in extensions)
    in_some = any(alpha in ext for ext in extensions)

    if in_all:
        return "skeptically accepted"
    if in_some:
        return "credulously accepted"
    return "rejected"


def report_detailed_acceptance_status(
    af: ArgumentationFramework,
    alpha: str,
    semantics: str = "preferred",
) -> Dict[str, object]:
    """
    Return both the mutually-exclusive status label and the exact Definition 5.8
    boolean predicates (`skeptically_accepted`, `credulously_accepted`, `rejected`).
    """
    status = report_acceptance_status(af, alpha, semantics=semantics)
    return {
        "argument": alpha,
        "semantics": semantics,
        "status": status,
        "skeptically_accepted": status == "skeptically accepted",
        "credulously_accepted": status in ("skeptically accepted", "credulously accepted"),
        "rejected": status == "rejected",
    }
