"""
src/strategic.py

Strategic Argumentation & Grounded Direct Argumentation Mechanism (Part 2: Items 1-4).

Implements:
1. `grounded_direct_mechanism`: Evaluates the grounded extension of the subgraph
   induced by the union of revealed argument subsets.
2. `find_best_responses`: Enumerates all subsets S subseteq A_i that agent i
   could reveal (given fixed reports by other agents) and returns the reports
   maximizing agent i's utility |A_i cap E_grnd|.
3. `check_theorem_5_3_strategyproof`: Verifies exact strategyproofness (Theorem 5.3)
   by testing whether truthful revelation (revealing all of A_i) is a best response
   for every agent i against every combination of subsets revealed by A_{-i}.
4. `check_theorem_5_4_condition`: Checks the graph-theoretic sufficient condition
   (Theorem 5.4) that no agent holds two arguments alpha, beta in A_i with an
   odd-length directed path from alpha to beta in the full graph, carefully
   handling cycles and reconvergent paths.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from itertools import combinations, product
from typing import Dict, FrozenSet, Iterable, List, Mapping, Sequence, Set, Tuple

from src.framework import ArgumentationFramework
from src.semantics import compute_grounded_extension


def powerset(iterable: Iterable[str]) -> List[Set[str]]:
    """
    Return all subsets of `iterable` in deterministic order (from empty set
    to the full set).
    """
    items = sorted(set(iterable))
    result: List[Set[str]] = []
    for r in range(len(items) + 1):
        for comb in combinations(items, r):
            result.append(set(comb))
    return result


# ============================================================================
# Part 2, Item 1: Grounded Direct Argumentation Mechanism
# ============================================================================


def grounded_direct_mechanism(
    global_af: ArgumentationFramework,
    revealed_reports: Mapping[str, Iterable[str]] | Sequence[Iterable[str]],
) -> Set[str]:
    """
    Part 2, Item 1: The Grounded Direct Argumentation Mechanism M_AF^grnd.

    Takes the global argumentation framework (or attack relation) and one
    revealed argument set A_i^o per agent i, and returns the grounded extension
    of the subgraph induced by the union of the revealed arguments:
        g(A_1^o, ..., A_n^o) = E_grnd(AF|_{A_1^o cup ... cup A_n^o})
    """
    if isinstance(revealed_reports, Mapping):
        report_sets = revealed_reports.values()
    else:
        report_sets = revealed_reports

    union_revealed: Set[str] = set()
    for rep in report_sets:
        union_revealed.update(rep)

    induced_af = global_af.induced_subgraph(union_revealed)
    return compute_grounded_extension(induced_af)


def compute_agent_utility(
    agent_true_args: Iterable[str],
    accepted_extension: Iterable[str],
) -> int:
    """
    Compute agent i's utility under individual acceptability-maximizing preferences:
        u_i(o) = |A_i cap o|
    where A_i is agent i's true argument set and o is the accepted grounded extension.
    """
    return len(set(agent_true_args).intersection(accepted_extension))


# ============================================================================
# Part 2, Item 2: Enumerate Subsets and Find Utility-Maximizing Best Responses
# ============================================================================


@dataclass(frozen=True)
class BestResponseResult:
    """
    Detailed result of enumerating all possible subsets agent i can reveal.
    """

    agent_id: str
    true_args: FrozenSet[str]
    max_utility: int
    truthful_utility: int
    best_reports: List[Set[str]]
    utility_by_report: List[Tuple[Set[str], int, Set[str]]]

    @property
    def can_gain_by_hiding(self) -> bool:
        """True iff some strict subset achieves strictly higher utility than truthfulness."""
        return self.max_utility > self.truthful_utility


def find_best_responses(
    global_af: ArgumentationFramework,
    agent_id: str,
    agent_true_args: Iterable[str],
    other_agents_reports: Mapping[str, Iterable[str]] | Sequence[Iterable[str]],
) -> BestResponseResult:
    """
    Part 2, Item 2: Enumerate every subset of A_i that agent i could reveal,
    given fixed reports by the other agents, and return the reports that
    maximize agent i's utility.
    """
    a_i = set(agent_true_args)
    if isinstance(other_agents_reports, Mapping):
        others_union: Set[str] = set()
        for k, v in other_agents_reports.items():
            if k != agent_id:
                others_union.update(v)
    else:
        others_union = set()
        for v in other_agents_reports:
            others_union.update(v)

    all_subsets = powerset(a_i)
    utility_records: List[Tuple[Set[str], int, Set[str]]] = []
    max_u = -1
    truthful_u = 0

    for subset in all_subsets:
        outcome = grounded_direct_mechanism(global_af, [subset, others_union])
        u = compute_agent_utility(a_i, outcome)
        utility_records.append((subset, u, outcome))
        if u > max_u:
            max_u = u
        if subset == a_i:
            truthful_u = u

    best_reports = [subset for subset, u, _ in utility_records if u == max_u]
    return BestResponseResult(
        agent_id=agent_id,
        true_args=frozenset(a_i),
        max_utility=max_u,
        truthful_utility=truthful_u,
        best_reports=best_reports,
        utility_by_report=utility_records,
    )


# ============================================================================
# Part 2, Item 3: Verify Theorem 5.3 (Exact Strategyproofness Check)
# ============================================================================


@dataclass(frozen=True)
class ManipulationWitness:
    """
    Records a concrete counterexample profile when a mechanism fails Theorem 5.3
    (i.e., an agent strictly benefits by hiding arguments).
    """

    manipulating_agent: str
    true_type: FrozenSet[str]
    other_agents_reports: Dict[str, FrozenSet[str]]
    truthful_outcome: FrozenSet[str]
    truthful_utility: int
    profitable_report: FrozenSet[str]
    manipulated_outcome: FrozenSet[str]
    manipulated_utility: int


@dataclass(frozen=True)
class Theorem53Result:
    """
    Result of checking Theorem 5.3 across all agents and all report profiles.
    """

    is_strategyproof: bool
    witness: ManipulationWitness | None = None


def check_theorem_5_3_strategyproof(
    global_af: ArgumentationFramework,
    agent_types: Mapping[str, Iterable[str]],
) -> Theorem53Result:
    """
    Part 2, Item 3: Check if a given argumentation framework with grounded direct
    argumentation mechanism satisfies Theorem 5.3 by verifying if for every agent i,
    revealing all of A_i (truthfulness) is a best response against every combination
    of subsets the other agents could reveal:

        forall i in I, forall S subseteq A_i, forall A_{-i}^o subseteq A_{-i}:
            |A_i cap E_grnd(A_i cup A_{-i}^o)| >= |A_i cap E_grnd((A_i \\ S) cup A_{-i}^o)|

    Optimization:
    Since the mechanism outcome depends only on the union of revealed arguments
    A^o = A_1^o cup ... cup A_n^o, we memoize `E_grnd(AF|_{A^o})` keyed by
    `frozenset(A^o)`. For |A| <= 8, at most 2^8 = 256 induced grounded extensions
    are ever computed.
    """
    agents = list(agent_types.keys())
    clean_types: Dict[str, Set[str]] = {
        ag: set(agent_types[ag]) for ag in agents
    }
    agent_powersets: Dict[str, List[Set[str]]] = {
        ag: powerset(clean_types[ag]) for ag in agents
    }

    # Memoization cache: frozenset(revealed_union) -> frozenset(grounded_extension)
    grounded_cache: Dict[FrozenSet[str], FrozenSet[str]] = {}

    def get_grounded(revealed_union: FrozenSet[str]) -> FrozenSet[str]:
        if revealed_union not in grounded_cache:
            induced = global_af.induced_subgraph(revealed_union)
            grounded_cache[revealed_union] = frozenset(
                compute_grounded_extension(induced)
            )
        return grounded_cache[revealed_union]

    for i_idx, agent_i in enumerate(agents):
        a_i = clean_types[agent_i]
        if not a_i:
            continue

        other_agents = [ag for idx, ag in enumerate(agents) if idx != i_idx]
        other_spaces = [agent_powersets[ag] for ag in other_agents]

        # Iterate over every combination of subsets the other agents could reveal
        for other_profile in product(*other_spaces):
            others_union: Set[str] = set()
            for rep in other_profile:
                others_union.update(rep)

            truthful_union = frozenset(a_i | others_union)
            truthful_outcome = get_grounded(truthful_union)
            truthful_u = len(a_i & truthful_outcome)

            # Check every subset A_i^o subseteq A_i that agent_i could reveal
            for subset_i in agent_powersets[agent_i]:
                if len(subset_i) <= truthful_u:
                    # A revealed subset of size <= truthful_u can yield at most
                    # len(subset_i) <= truthful_u accepted arguments, so it can
                    # never strictly beat `truthful_u`!
                    continue

                dev_union = frozenset(subset_i | others_union)
                dev_outcome = get_grounded(dev_union)
                dev_u = len(a_i & dev_outcome)

                if dev_u > truthful_u:
                    other_dict = {
                        other_agents[k]: frozenset(other_profile[k])
                        for k in range(len(other_agents))
                    }
                    witness = ManipulationWitness(
                        manipulating_agent=agent_i,
                        true_type=frozenset(a_i),
                        other_agents_reports=other_dict,
                        truthful_outcome=truthful_outcome,
                        truthful_utility=truthful_u,
                        profitable_report=frozenset(subset_i),
                        manipulated_outcome=dev_outcome,
                        manipulated_utility=dev_u,
                    )
                    return Theorem53Result(is_strategyproof=False, witness=witness)

    return Theorem53Result(is_strategyproof=True, witness=None)


# ============================================================================
# Part 2, Item 4: Verify Theorem 5.4 (Odd-Length Directed Path with Cycles)
# ============================================================================


@dataclass(frozen=True)
class OddPathViolation:
    """
    Witness when Theorem 5.4's condition fails: an agent holds arguments
    alpha, beta in A_i with an odd-length directed path from alpha to beta.
    """

    agent: str
    source: str
    target: str
    odd_path: Tuple[str, ...]

    @property
    def length(self) -> int:
        """Number of directed edges in the path (always odd: 1, 3, 5, ...)."""
        return len(self.odd_path) - 1


@dataclass(frozen=True)
class Theorem54Result:
    """
    Result of checking Theorem 5.4's graph-theoretic condition.
    """

    condition_holds: bool
    violations: List[OddPathViolation]


def find_odd_length_simple_path(
    af: ArgumentationFramework,
    source: str,
    target: str,
) -> Tuple[str, ...] | None:
    """
    Search for an odd-length simple directed path from `source` to `target` in `af`.

    Cycle Handling Details:
    -----------------------
    Why does a naive BFS/DFS fail when the graph contains cycles?
    In a standard graph traversal that maintains a single global `visited` set
    of vertices, if a vertex `v` is first reached from `source` via an EVEN-length
    prefix (or via a cycle), `v` is marked visited and never explored again with
    an ODD-length prefix! As a result, a naive search misses valid odd-length
    paths whenever an even-length path or cycle shares intermediate vertices.

    To handle cycles accurately:
    We perform backtracking DFS with path-local cycle detection (`on_path`),
    allowing a vertex `v` to be explored under both parities across different
    branches while preventing infinite loops around cycles on the current branch.
    If `source == target`, a non-empty simple cycle of odd length starting and
    ending at `source` (including a self-loop `source -> source` of length 1)
    is also detected.
    """
    path: List[str] = [source]
    on_path: Set[str] = {source}

    def dfs(current: str, parity: int) -> Tuple[str, ...] | None:
        for nxt in af.ordered_arguments:
            if nxt not in af.attacked_by(current):
                continue
            next_parity = 1 - parity

            # Check if we reached `target` in an odd number of edges
            if nxt == target and next_parity == 1:
                return tuple(path + [nxt])

            # Continue exploring simple paths without repeating vertices on the current branch
            if nxt not in on_path:
                on_path.add(nxt)
                path.append(nxt)
                res = dfs(nxt, next_parity)
                if res is not None:
                    return res
                path.pop()
                on_path.remove(nxt)
        return None

    return dfs(source, 0)


def find_odd_length_walk(
    af: ArgumentationFramework,
    source: str,
    target: str,
) -> Tuple[str, ...] | None:
    """
    Search for a shortest odd-length directed walk (allowing cycle traversal)
    from `source` to `target` using Parity-State Breadth-First Search on the
    product state space V x {0, 1}.

    State `(u, p)` means vertex `u` is reachable from `source` in a walk of
    length congruent to `p` (mod 2). Because there are at most 2|A| states,
    this terminates in O(|A| + |R|) time even in heavily cyclic graphs and never
    enters an infinite loop.
    """
    start_state = (source, 0)
    queue: deque[Tuple[str, int]] = deque([start_state])
    parent: Dict[Tuple[str, int], Tuple[str, int] | None] = {start_state: None}

    while queue:
        u, parity = queue.popleft()
        next_parity = 1 - parity
        for v in sorted(af.attacked_by(u)):
            next_state = (v, next_parity)
            if next_state not in parent:
                parent[next_state] = (u, parity)
                if v == target and next_parity == 1:
                    # Reconstruct the shortest odd walk
                    walk: List[str] = []
                    curr: Tuple[str, int] | None = next_state
                    while curr is not None:
                        walk.append(curr[0])
                        curr = parent[curr]
                    walk.reverse()
                    return tuple(walk)
                queue.append(next_state)

    return None


def check_theorem_5_4_condition(
    global_af: ArgumentationFramework,
    agent_types: Mapping[str, Iterable[str]],
    allow_walks: bool = True,
    distinct_only: bool = False,
) -> Theorem54Result:
    """
    Part 2, Item 4: Check if a grounded direct argumentation mechanism is
    strategyproof via Theorem 5.4 by verifying that no agent holds two arguments
    alpha, beta in A_i with an odd-length directed path from alpha to beta in the
    full graph.

    Parameters:
      - `global_af`: The full argumentation framework <A, -> >.
      - `agent_types`: Mapping from agent identifier to its set of arguments A_i.
      - `allow_walks`: If True (default), uses parity-state BFS (`find_odd_length_walk`)
        which detects any odd-length directed path/walk in the presence of cycles
        (falling back to `find_odd_length_simple_path` when a simple path exists).
      - `distinct_only`: If False (default), checks all pairs (alpha, beta) in A_i x A_i
        (matching the formal statement in Theorem 5.4: "not exists alpha_1, alpha_2 in A_i
        such that alpha_1 ->_odd alpha_2"). If True, checks only alpha != beta.
    """
    violations: List[OddPathViolation] = []

    for agent_id, args_iter in agent_types.items():
        a_i = sorted(set(args_iter))
        for alpha in a_i:
            for beta in a_i:
                if distinct_only and alpha == beta:
                    continue

                # Prefer a simple odd path if one exists; otherwise check odd walk via cycles
                odd_path = find_odd_length_simple_path(global_af, alpha, beta)
                if odd_path is None and allow_walks:
                    odd_path = find_odd_length_walk(global_af, alpha, beta)

                if odd_path is not None:
                    violations.append(
                        OddPathViolation(
                            agent=agent_id,
                            source=alpha,
                            target=beta,
                            odd_path=odd_path,
                        )
                    )

    return Theorem54Result(
        condition_holds=(len(violations) == 0),
        violations=violations,
    )
