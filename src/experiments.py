"""
src/experiments.py

Monte Carlo Experiment Suite & Game-Theoretic Outcome Analyzer for Strategic
Argumentation (Part 2: Experiments).

Specification:
  - Given 3 agents, generate at least 1000 random instances:
      * 6 to 8 arguments
      * each possible attack present with probability p in {0.15, 0.25, 0.35}
      * arguments split at random among 3 agents
  - For each instance, record whether the mechanism is strategyproof (Theorem 5.3)
    and whether Theorem 5.4's condition holds.
  - Report:
      1. The fraction of instances that are strategyproof, for each p.
      2. How many instances satisfy the condition in Theorem 5.4 yet fail
         strategyproofness. Note these instances and explain.
      3. Are there instances that are strategyproof although the condition fails?
         Note these instances and check why they are strategyproof.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from itertools import product
import random
from typing import Dict, FrozenSet, List, Set, Tuple

from src.framework import ArgumentationFramework
from src.semantics import compute_grounded_extension
from src.strategic import (
    ManipulationWitness,
    OddPathViolation,
    check_theorem_5_3_strategyproof,
    check_theorem_5_4_condition,
    powerset,
)


@dataclass(frozen=True)
class SubsetDeviationRow:
    """
    Exact grounded-outcome comparison for a single revealed subset S subseteq A_i
    against a fixed opponent report profile A_{-i}^o.
    """

    revealed_subset: FrozenSet[str]
    induced_grounded: FrozenSet[str]
    accepted_own: FrozenSet[str]
    rescued_args: FrozenSet[str]     # G(S) = (A_i cap E_dev) \ E_truth
    sacrificed_args: FrozenSet[str]  # L(S) = (A_i cap E_truth) \ E_dev
    utility: int


@dataclass(frozen=True)
class VerifiedStrategyproofExplanation:
    """
    Mathematically verified explanation of why an instance is strategyproof
    (Theorem 5.3 holds) despite failing Theorem 5.4's graph condition.

    Computed by exhaustively evaluating E_truth = E_grnd(A_i cup A_{-i}^o)
    and E_dev = E_grnd(S cup A_{-i}^o) across ALL agents i, ALL opponent
    report profiles A_{-i}^o, and ALL subsets S subseteq A_i, and checking
    the rescued set G(S) = (A_i cap E_dev) \\ E_truth and sacrificed set
    L(S) = (A_i cap E_truth) \\ E_dev.
    """

    category: str
    max_rescued_in_any_profile: int
    focus_agent: str
    focus_violation: OddPathViolation
    witness_opponent_reports: Dict[str, FrozenSet[str]]
    truthful_outcome: FrozenSet[str]
    truthful_utility: int
    deviation_table: List[SubsetDeviationRow]


@dataclass
class InstanceRecord:
    """
    Complete record of a single random strategic argumentation instance.
    """

    instance_id: int
    p: float
    num_args: int
    af: ArgumentationFramework
    agent_types: Dict[str, Set[str]]
    is_strategyproof: bool
    theorem_5_4_holds: bool
    theorem_5_4_distinct_holds: bool
    theorem_5_4_simple_all_holds: bool
    theorem_5_4_simple_distinct_holds: bool
    witness: ManipulationWitness | None = None
    violations: List[OddPathViolation] = field(default_factory=list)
    verified_explanation: VerifiedStrategyproofExplanation | None = None


@dataclass
class ProbabilityBucketSummary:
    """
    Aggregated experimental results for a single attack probability p.
    """

    p: float
    total_instances: int
    strategyproof_count: int
    theorem_5_4_holds_count: int
    theorem_5_4_distinct_holds_count: int
    theorem_5_4_simple_all_holds_count: int
    theorem_5_4_simple_distinct_holds_count: int
    t54_holds_but_not_sp_count: int
    t54_distinct_holds_but_not_sp_count: int
    t54_simple_holds_but_not_sp_count: int
    only_len_1_not_sp_count: int
    sp_although_t54_fails_count: int
    both_fail_count: int
    t54_holds_but_not_sp_examples: List[InstanceRecord]
    sp_although_t54_fails_examples: List[InstanceRecord]
    not_sp_examples: List[InstanceRecord]
    reason_breakdown: Dict[str, int]

    @property
    def strategyproof_fraction(self) -> float:
        return (
            self.strategyproof_count / self.total_instances
            if self.total_instances
            else 0.0
        )

    @property
    def theorem_5_4_holds_fraction(self) -> float:
        return (
            self.theorem_5_4_holds_count / self.total_instances
            if self.total_instances
            else 0.0
        )


def generate_random_instance(
    rng: random.Random,
    p: float,
    instance_id: int = 0,
    min_args: int = 6,
    max_args: int = 8,
    allow_self_attacks: bool = True,
    require_non_empty_agents: bool = True,
) -> Tuple[ArgumentationFramework, Dict[str, Set[str]]]:
    """
    Generate a single random instance with:
      1. `n` chosen uniformly from `{6, 7, 8}`, producing arguments `a1, ..., an`.
      2. Each possible directed attack `(au, av) in A x A` included independently
         with probability `p`:
         - When `allow_self_attacks=True` (default), all `n^2` ordered pairs
           (including self-attacks `au -> au`) are sampled independently with
           probability `p`.
         - When `allow_self_attacks=False`, only the `n(n-1)` distinct ordered
           pairs `au != av` are sampled.
      3. Arguments split at random among 3 agents (`Agent_1`, `Agent_2`, `Agent_3`):
         - When `require_non_empty_agents=True` (default), the arguments are
           shuffled, 1 argument is assigned to each of the 3 agents so every
           agent holds a non-empty set (`A_i != empty`), and the remaining
           `n - 3` arguments are distributed uniformly at random among the 3 agents.
         - When `require_non_empty_agents=False`, all `n` arguments are assigned
           independently and uniformly at random to the 3 agents.
    """
    n = rng.randint(min_args, max_args)
    args = [f"a{i}" for i in range(1, n + 1)]

    attacks: List[Tuple[str, str]] = []
    for u in args:
        for v in args:
            if not allow_self_attacks and u == v:
                continue
            if rng.random() < p:
                attacks.append((u, v))

    af = ArgumentationFramework(arguments=args, attacks=attacks)

    agent_names = ["Agent_1", "Agent_2", "Agent_3"]
    agent_types: Dict[str, Set[str]] = {name: set() for name in agent_names}

    if require_non_empty_agents and n >= len(agent_names):
        shuffled = list(args)
        rng.shuffle(shuffled)
        for idx, name in enumerate(agent_names):
            agent_types[name].add(shuffled[idx])
        for arg in shuffled[len(agent_names) :]:
            chosen_agent = rng.choice(agent_names)
            agent_types[chosen_agent].add(arg)
    else:
        for arg in args:
            chosen_agent = rng.choice(agent_names)
            agent_types[chosen_agent].add(arg)

    return af, agent_types


def select_representative_violation(
    violations: List[OddPathViolation],
    preferred_agent: str | None = None,
    preferred_sources: FrozenSet[str] | None = None,
    preferred_targets: FrozenSet[str] | None = None,
) -> OddPathViolation:
    """
    Select the most informative odd-path violation from `violations` for reporting:
      1. If `preferred_agent`, `preferred_sources`, and `preferred_targets` are
         provided (e.g., from an active rescue profile where hiding `preferred_sources`
         rescues `preferred_targets`), prioritize violations matching that exact
         causal (agent, source, target) triple.
      2. Always prefer simple odd paths (`is_simple_path=True`, no repeated vertices)
         between distinct arguments (`source != target`) over walks that repeat
         cycle vertices.
      3. Prefer indirect simple odd paths (length >= 3) over direct attacks (length 1)
         when both are simple paths.
    """
    pool = violations
    if preferred_agent is not None:
        agent_pool = [v for v in pool if v.agent == preferred_agent]
        if agent_pool:
            pool = agent_pool

    if preferred_sources and preferred_targets:
        causal_pool = [
            v
            for v in pool
            if v.source in preferred_sources and v.target in preferred_targets
        ]
        if causal_pool:
            pool = causal_pool

    distinct = [v for v in pool if v.source != v.target]
    simple_indirect = [v for v in distinct if v.is_simple_path and v.length >= 3]
    if simple_indirect:
        return simple_indirect[0]
    simple_direct = [v for v in distinct if v.is_simple_path]
    if simple_direct:
        return simple_direct[0]
    walk_indirect = [v for v in distinct if v.length >= 3]
    if walk_indirect:
        return walk_indirect[0]
    if distinct:
        return distinct[0]
    return pool[0]


def verify_why_strategyproof_despite_t54_failure(
    af: ArgumentationFramework,
    agent_types: Dict[str, Set[str]],
    violations: List[OddPathViolation],
) -> VerifiedStrategyproofExplanation:
    """
    Genuine Game-Theoretic & Grounded-Outcome Structural Verifier (Question 3).

    Instead of guessing from path lengths, this function exhaustively evaluates
    the grounded outcomes across ALL agents i, ALL opponent report combinations
    A_{-i}^o subseteq A_{-i}, and ALL subsets S subseteq A_i.

    For every profile (i, A_{-i}^o, S), let:
      - E_truth = E_grnd(A_i cup A_{-i}^o)
      - E_dev   = E_grnd(S cup A_{-i}^o)
      - G(S, A_{-i}^o) = (A_i cap E_dev) \\ E_truth
            (arguments of A_i RESCUED by hiding A_i \\ S)
      - L(S, A_{-i}^o) = (A_i cap E_truth) \\ E_dev
            (arguments of A_i SACRIFICED by hiding A_i \\ S)

    Because the instance satisfies Theorem 5.3 (strategyproofness), every profile
    satisfies |G(S, A_{-i}^o)| <= |L(S, A_{-i}^o)| (verified by assertion below).

    We then classify the instance into one of four mathematically verified,
    mutually-exclusive categories based on the actual behavior of G and L across
    all profiles:

    1. "1A. Self-Attack / Odd Self-Cycle Only (alpha == beta, |G| = 0 in all profiles)":
       Every odd-length path/walk in A_i has source == target (e.g. a self-loop
       alpha -> alpha or odd cycle alpha -> ... -> alpha). Hiding alpha removes
       alpha from the induced graph, so |G| == 0 across all profiles.

    2. "1B. Path Cancelled / Target Always Accepted Under Truthfulness (|G| = 0 in all profiles, Example 5.11 Type)":
       Distinct-argument odd paths (alpha -> ... -> beta) exist, |G| == 0 across
       all profiles (hiding never rescues any argument), and the target beta of
       the representative violation is accepted under truthful revelation (because
       an intermediate attacker on the odd path is defeated, as in Example 5.11).

    3. "1C. Target Unrescuable / Blocked Even When Source Hidden (|G| = 0 in all profiles)":
       Distinct-argument odd paths (alpha -> ... -> beta) exist and |G| == 0 across
       all profiles: whenever beta is not accepted under truthfulness, hiding alpha
       (or any subset of A_i) still fails to make beta accepted because beta has
       independent undefeated attackers, self-loops, or cycles, or alpha itself
       was already defeated.

    4. "2. Active Rescue Offset by Equal/Greater Sacrifice (|G| >= 1 in some profile, but |L| >= |G| everywhere)":
       There exists at least one opponent profile A_{-i}^o and deviation S subsetneq A_i
       where hiding A_i \\ S genuinely rescues one or more arguments (|G(S)| >= 1),
       AND in every such profile the number of previously accepted arguments lost
       by hiding A_i \\ S is at least as large (|L(S)| >= |G(S)| >= 1), yielding
       net utility change |G| - |L| <= 0.
    """
    agents = list(agent_types.keys())
    clean_types: Dict[str, Set[str]] = {ag: set(agent_types[ag]) for ag in agents}
    agent_powersets: Dict[str, List[Set[str]]] = {
        ag: powerset(clean_types[ag]) for ag in agents
    }

    grounded_cache: Dict[FrozenSet[str], FrozenSet[str]] = {}

    def get_grounded(revealed_union: FrozenSet[str]) -> FrozenSet[str]:
        if revealed_union not in grounded_cache:
            induced = af.induced_subgraph(revealed_union)
            grounded_cache[revealed_union] = frozenset(
                compute_grounded_extension(induced)
            )
        return grounded_cache[revealed_union]

    focus_viol = select_representative_violation(violations)
    focus_agent = focus_viol.agent

    max_rescued = 0
    best_rescue_witness: Tuple[
        str, Dict[str, FrozenSet[str]], FrozenSet[str], List[SubsetDeviationRow]
    ] | None = None
    default_focus_witness: Tuple[
        str, Dict[str, FrozenSet[str]], FrozenSet[str], List[SubsetDeviationRow]
    ] | None = None

    target_accepted_truthfully_in_full = False

    for i_idx, agent_i in enumerate(agents):
        a_i = clean_types[agent_i]
        if not a_i:
            continue
        a_i_frozen = frozenset(a_i)
        other_agents = [ag for idx, ag in enumerate(agents) if idx != i_idx]
        other_spaces = [agent_powersets[ag] for ag in other_agents]

        for other_profile in product(*other_spaces):
            others_union: Set[str] = set()
            for rep in other_profile:
                others_union.update(rep)

            truthful_union = frozenset(a_i | others_union)
            e_truth = get_grounded(truthful_union)
            own_truth = a_i_frozen & e_truth

            # Check if this is the full truthful profile of the other agents
            is_others_full_truthful = all(
                other_profile[k] == clean_types[other_agents[k]]
                for k in range(len(other_agents))
            )
            if agent_i == focus_agent and is_others_full_truthful:
                if focus_viol.target in own_truth:
                    target_accepted_truthfully_in_full = True

            profile_rows: List[SubsetDeviationRow] = []
            profile_max_g = 0

            for subset_s in agent_powersets[agent_i]:
                s_frozen = frozenset(subset_s)
                e_dev = get_grounded(frozenset(subset_s | others_union))
                own_dev = a_i_frozen & e_dev

                rescued = own_dev - own_truth
                sacrificed = own_truth - own_dev

                # Mathematical verification: in a strategyproof instance,
                # rescued arguments can never exceed sacrificed arguments!
                assert len(rescued) <= len(sacrificed), (
                    f"Strategyproofness violated for {agent_i}: "
                    f"|G|={len(rescued)} > |L|={len(sacrificed)}"
                )

                if len(rescued) > profile_max_g:
                    profile_max_g = len(rescued)

                profile_rows.append(
                    SubsetDeviationRow(
                        revealed_subset=s_frozen,
                        induced_grounded=e_dev,
                        accepted_own=own_dev,
                        rescued_args=rescued,
                        sacrificed_args=sacrificed,
                        utility=len(own_dev),
                    )
                )

            other_dict = {
                other_agents[k]: frozenset(other_profile[k])
                for k in range(len(other_agents))
            }

            if agent_i == focus_agent and is_others_full_truthful:
                default_focus_witness = (agent_i, other_dict, e_truth, profile_rows)

            if profile_max_g > max_rescued:
                max_rescued = profile_max_g
                best_rescue_witness = (agent_i, other_dict, e_truth, profile_rows)

    distinct_violations = [v for v in violations if v.source != v.target]
    if not distinct_violations:
        assert max_rescued == 0
        category = (
            "1A. Self-Attack / Odd Self-Cycle Only "
            "(alpha == beta, verified |G| = 0 across all profiles)"
        )
        chosen_witness = default_focus_witness
    elif max_rescued > 0:
        category = (
            "2. Active Rescue Offset by Equal/Greater Sacrifice "
            "(verified |G| >= 1 in some profile, but |L| >= |G| in all profiles)"
        )
        chosen_witness = best_rescue_witness
    elif target_accepted_truthfully_in_full:
        category = (
            "1B. Path Cancelled / Target Accepted Under Truthfulness "
            "(verified |G| = 0 in all profiles, Example 5.11 Type)"
        )
        chosen_witness = default_focus_witness
    else:
        category = (
            "1C. Target Unrescuable / Independently Blocked "
            "(verified |G| = 0 in all profiles)"
        )
        chosen_witness = default_focus_witness

    assert chosen_witness is not None
    w_agent, w_others, w_e_truth, w_rows = chosen_witness
    w_truth_u = len(clean_types[w_agent] & w_e_truth)

    # If an active rescue occurred in `chosen_witness`, align `focus_viol` with
    # the exact hidden-source -> rescued-target pair in `w_rows`!
    if max_rescued > 0:
        for r in w_rows:
            if len(r.rescued_args) == max_rescued:
                hidden_args = frozenset(clean_types[w_agent]) - r.revealed_subset
                focus_viol = select_representative_violation(
                    violations,
                    preferred_agent=w_agent,
                    preferred_sources=hidden_args,
                    preferred_targets=r.rescued_args,
                )
                break

    return VerifiedStrategyproofExplanation(
        category=category,
        max_rescued_in_any_profile=max_rescued,
        focus_agent=w_agent,
        focus_violation=focus_viol,
        witness_opponent_reports=w_others,
        truthful_outcome=w_e_truth,
        truthful_utility=w_truth_u,
        deviation_table=w_rows,
    )


def run_experiments(
    num_instances_per_p: int = 1000,
    probabilities: Tuple[float, ...] = (0.15, 0.25, 0.35),
    seed: int = 42,
    allow_self_attacks: bool = True,
    require_non_empty_agents: bool = True,
) -> Dict[float, ProbabilityBucketSummary]:
    """
    Run the Monte Carlo experiment suite across all `p in probabilities`.
    Generates `num_instances_per_p` random instances for EACH probability `p`
    (total = 3 * num_instances_per_p = 3000 instances by default).
    """
    rng = random.Random(seed)
    summaries: Dict[float, ProbabilityBucketSummary] = {}

    global_id = 0
    for p in probabilities:
        sp_count = 0
        t54_count = 0
        t54_distinct_count = 0
        t54_simple_all_count = 0
        t54_simple_distinct_count = 0

        t54_holds_not_sp = 0
        t54_distinct_holds_not_sp = 0
        t54_simple_holds_not_sp = 0
        only_len_1_not_sp = 0

        sp_but_t54_fails = 0
        both_fail = 0

        t54_holds_not_sp_examples: List[InstanceRecord] = []
        sp_but_t54_fails_examples: List[InstanceRecord] = []
        not_sp_examples: List[InstanceRecord] = []
        reason_counts: Dict[str, int] = {}

        for _ in range(num_instances_per_p):
            global_id += 1
            af, agent_types = generate_random_instance(
                rng=rng,
                p=p,
                instance_id=global_id,
                allow_self_attacks=allow_self_attacks,
                require_non_empty_agents=require_non_empty_agents,
            )

            t53_res = check_theorem_5_3_strategyproof(af, agent_types)
            t54_res = check_theorem_5_4_condition(
                af, agent_types, allow_walks=True, distinct_only=False
            )
            t54_distinct_res = check_theorem_5_4_condition(
                af, agent_types, allow_walks=True, distinct_only=True
            )
            t54_simple_all_res = check_theorem_5_4_condition(
                af, agent_types, allow_walks=False, distinct_only=False
            )
            t54_simple_distinct_res = check_theorem_5_4_condition(
                af, agent_types, allow_walks=False, distinct_only=True
            )

            is_sp = t53_res.is_strategyproof
            t54_holds = t54_res.condition_holds

            verified_exp: VerifiedStrategyproofExplanation | None = None
            if is_sp and not t54_holds:
                verified_exp = verify_why_strategyproof_despite_t54_failure(
                    af, agent_types, t54_res.violations
                )
                cat = verified_exp.category
                reason_counts[cat] = reason_counts.get(cat, 0) + 1

            record = InstanceRecord(
                instance_id=global_id,
                p=p,
                num_args=len(af.arguments),
                af=af,
                agent_types=agent_types,
                is_strategyproof=is_sp,
                theorem_5_4_holds=t54_holds,
                theorem_5_4_distinct_holds=t54_distinct_res.condition_holds,
                theorem_5_4_simple_all_holds=t54_simple_all_res.condition_holds,
                theorem_5_4_simple_distinct_holds=t54_simple_distinct_res.condition_holds,
                witness=t53_res.witness,
                violations=t54_res.violations,
                verified_explanation=verified_exp,
            )

            if is_sp:
                sp_count += 1
            if t54_holds:
                t54_count += 1
            if t54_distinct_res.condition_holds:
                t54_distinct_count += 1
            if t54_simple_all_res.condition_holds:
                t54_simple_all_count += 1
            if t54_simple_distinct_res.condition_holds:
                t54_simple_distinct_count += 1

            if not is_sp:
                if t54_holds:
                    t54_holds_not_sp += 1
                    if len(t54_holds_not_sp_examples) < 5:
                        t54_holds_not_sp_examples.append(record)
                if t54_distinct_res.condition_holds:
                    t54_distinct_holds_not_sp += 1
                if t54_simple_all_res.condition_holds:
                    t54_simple_holds_not_sp += 1
                if not any(v.length >= 3 for v in t54_res.violations):
                    only_len_1_not_sp += 1

            if is_sp and not t54_holds:
                sp_but_t54_fails += 1
                if len(sp_but_t54_fails_examples) < 5:
                    sp_but_t54_fails_examples.append(record)
            elif not is_sp and not t54_holds:
                both_fail += 1
                if len(not_sp_examples) < 5:
                    not_sp_examples.append(record)

        summaries[p] = ProbabilityBucketSummary(
            p=p,
            total_instances=num_instances_per_p,
            strategyproof_count=sp_count,
            theorem_5_4_holds_count=t54_count,
            theorem_5_4_distinct_holds_count=t54_distinct_count,
            theorem_5_4_simple_all_holds_count=t54_simple_all_count,
            theorem_5_4_simple_distinct_holds_count=t54_simple_distinct_count,
            t54_holds_but_not_sp_count=t54_holds_not_sp,
            t54_distinct_holds_but_not_sp_count=t54_distinct_holds_not_sp,
            t54_simple_holds_but_not_sp_count=t54_simple_holds_not_sp,
            only_len_1_not_sp_count=only_len_1_not_sp,
            sp_although_t54_fails_count=sp_but_t54_fails,
            both_fail_count=both_fail,
            t54_holds_but_not_sp_examples=t54_holds_not_sp_examples,
            sp_although_t54_fails_examples=sp_but_t54_fails_examples,
            not_sp_examples=not_sp_examples,
            reason_breakdown=reason_counts,
        )

    return summaries
