"""
src/framework.py

Core representation of Dung's Abstract Argumentation Framework <A, -> >
and foundational defense / characteristic functions (Items 1, 2, 3, 4).

Design Principles (SOLID):
- Single Responsibility: This module focuses solely on the graph structure of
  an argumentation framework and the fundamental defense / characteristic
  operations on argument sets.
- Open/Closed & Liskov Substitution: Provides clean, immutable query properties
  (`arguments`, `attacks`, `attackers_of`, `attacked_by`, `induced_subgraph`)
  that higher-level semantics and strategic mechanism modules build upon.
"""

from __future__ import annotations
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple


class ArgumentationFramework:
    """
    Represents an abstract argumentation framework AF = <A, -> >, where:
      - A is a finite set of abstract arguments.
      - -> subseteq A x A is a binary attack (defeat) relation.

    Internally maintains dual adjacency maps (`_attackers` and `_attacked`)
    so that conflict checks, defense checks, and range computations (S^+)
    execute in O(|S|) set operations rather than scanning all edges.
    """

    def __init__(
        self,
        arguments: Iterable[str] = (),
        attacks: Iterable[Tuple[str, str]] = (),
    ) -> None:
        self._arguments: Set[str] = set()
        self._attacks: Set[Tuple[str, str]] = set()
        # _attackers[alpha] = { beta in A | beta -> alpha } (incoming attacks)
        self._attackers: Dict[str, Set[str]] = {}
        # _attacked[alpha]  = { beta in A | alpha -> beta } (outgoing attacks)
        self._attacked: Dict[str, Set[str]] = {}

        for arg in arguments:
            self.add_argument(arg)
        for attacker, target in attacks:
            self.add_attack(attacker, target)

    def add_argument(self, arg: str) -> None:
        """Add a single argument to the framework."""
        if arg not in self._arguments:
            self._arguments.add(arg)
            self._attackers[arg] = set()
            self._attacked[arg] = set()

    def add_arguments(self, args: Iterable[str]) -> None:
        """Add multiple arguments to the framework."""
        for arg in args:
            self.add_argument(arg)

    def add_attack(self, attacker: str, target: str) -> None:
        """
        Add a directed attack (attacker -> target).
        If attacker or target is not yet in A, it is added automatically.
        """
        self.add_argument(attacker)
        self.add_argument(target)
        if (attacker, target) not in self._attacks:
            self._attacks.add((attacker, target))
            self._attacked[attacker].add(target)
            self._attackers[target].add(attacker)

    def add_attacks(self, attacks: Iterable[Tuple[str, str]]) -> None:
        """Add multiple directed attacks to the framework."""
        for attacker, target in attacks:
            self.add_attack(attacker, target)

    @property
    def arguments(self) -> FrozenSet[str]:
        """Return the immutable set of all arguments A."""
        return frozenset(self._arguments)

    @property
    def ordered_arguments(self) -> List[str]:
        """Return all arguments sorted deterministically."""
        return sorted(self._arguments)

    @property
    def attacks(self) -> FrozenSet[Tuple[str, str]]:
        """Return the immutable set of all attack pairs (alpha, beta) in ->."""
        return frozenset(self._attacks)

    def attackers_of(self, alpha: str) -> FrozenSet[str]:
        """
        Return { beta in A | beta -> alpha }, the set of direct attackers of alpha.
        Raises KeyError if alpha is not in A.
        """
        if alpha not in self._arguments:
            raise KeyError(f"Argument '{alpha}' is not in the argumentation framework.")
        return frozenset(self._attackers[alpha])

    def attacked_by(self, alpha: str) -> FrozenSet[str]:
        """
        Return { beta in A | alpha -> beta }, the set of arguments directly attacked by alpha.
        Raises KeyError if alpha is not in A.
        """
        if alpha not in self._arguments:
            raise KeyError(f"Argument '{alpha}' is not in the argumentation framework.")
        return frozenset(self._attacked[alpha])

    def set_attacked_by(self, S: Iterable[str]) -> FrozenSet[str]:
        """
        Compute S^+ = { beta in A | exists alpha in S such that alpha -> beta },
        the set of all arguments defeated/attacked by at least one member of S.
        """
        s_set = self._validate_subset(S)
        attacked: Set[str] = set()
        for alpha in s_set:
            attacked.update(self._attacked[alpha])
        return frozenset(attacked)

    def induced_subgraph(self, subset: Iterable[str]) -> ArgumentationFramework:
        """
        Construct the sub-framework AF|_subset = <subset, -> cap (subset x subset)>
        induced by a subset of arguments. Used heavily by the Grounded Direct
        Argumentation Mechanism when evaluating revealed argument subsets.
        """
        sub_set = set(subset)
        # Keep only attacks where both endpoints belong to sub_set
        induced_attacks = [
            (u, v) for (u, v) in self._attacks if u in sub_set and v in sub_set
        ]
        return ArgumentationFramework(arguments=sub_set, attacks=induced_attacks)

    def _validate_subset(self, S: Iterable[str]) -> Set[str]:
        """Convert S to a set and verify that all elements belong to A."""
        s_set = set(S)
        unknown = s_set - self._arguments
        if unknown:
            raise ValueError(
                f"Arguments {sorted(unknown)} do not belong to framework arguments {self.ordered_arguments}."
            )
        return s_set

    # Convenience methods delegating to the standalone functions
    def is_conflict_free(self, S: Iterable[str]) -> bool:
        """Test if S is conflict-free in this framework."""
        return is_conflict_free(self, S)

    def is_defended_by(self, alpha: str, S: Iterable[str]) -> bool:
        """Test if argument alpha is defended by S in this framework."""
        return is_defended_by(self, alpha, S)

    def characteristic_function(self, S: Iterable[str]) -> Set[str]:
        """Return F_AF(S), the set of arguments defended by S in this framework."""
        return characteristic_function(self, S)

    def __repr__(self) -> str:
        args_str = ", ".join(self.ordered_arguments)
        attacks_sorted = sorted(self._attacks)
        attacks_str = ", ".join(f"{u}->{v}" for u, v in attacks_sorted)
        return f"ArgumentationFramework(A={{{args_str}}}, R={{{attacks_str}}})"


# ============================================================================
# Standalone Functions Required by Part 1 (Items 2, 3, 4)
# ============================================================================


def is_conflict_free(af: ArgumentationFramework, S: Iterable[str]) -> bool:
    """
    Item 2: Test if a given set S of arguments is conflict-free.

    Definition (Dung 1995 / Rahwan Ch. 5, Def. 5.2):
    A set of arguments S subseteq A is conflict-free iff there are no
    arguments alpha, beta in S such that alpha -> beta.

    Equivalently, S cap S^+ == empty set.
    """
    s_set = af._validate_subset(S)
    # Check if any argument in S attacks any argument in S
    for alpha in s_set:
        # Disjointness test in CPython is O(min(|s_set|, |attacked_by(alpha)|))
        if not s_set.isdisjoint(af._attacked[alpha]):
            return False
    return True


def is_defended_by(af: ArgumentationFramework, alpha: str, S: Iterable[str]) -> bool:
    """
    Item 3: Test if a given argument alpha can be defended by a given set S.

    Definition (Dung 1995 / Rahwan Ch. 5, Def. 5.3):
    An argument alpha in A is defended by (or acceptable with respect to) a set
    S subseteq A iff for every argument beta in A that attacks alpha (beta -> alpha),
    there is some argument gamma in S that attacks beta (gamma -> beta).

    Equivalently, attackers_of(alpha) subseteq S^+.
    """
    if alpha not in af.arguments:
        raise ValueError(f"Argument '{alpha}' is not in the argumentation framework.")
    s_plus = af.set_attacked_by(S)
    # Every attacker beta of alpha must be defeated by at least one gamma in S
    return af.attackers_of(alpha).issubset(s_plus)


def characteristic_function(af: ArgumentationFramework, S: Iterable[str]) -> Set[str]:
    """
    Item 4: Characteristic function F_AF(S) to identify the set of arguments
    defended by a given set S.

    Definition (Dung 1995 / Rahwan Ch. 5, Def. 5.5):
    F_AF : 2^A -> 2^A is defined as:
        F_AF(S) = { alpha in A | alpha is defended by S }

    Optimization: Precomputes S^+ once, then checks `attackers_of(alpha) <= S^+`
    for each alpha in A.
    """
    s_plus = af.set_attacked_by(S)
    return {
        alpha
        for alpha in af.arguments
        if af.attackers_of(alpha).issubset(s_plus)
    }
