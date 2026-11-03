"""
src/experiments.py

Monte Carlo Experiment Suite for Strategic Argumentation (Part 2: Experiments).

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
import random
from typing import Dict, List, Set, Tuple

from src.framework import ArgumentationFramework
from src.strategic import (
    ManipulationWitness,
    OddPathViolation,
    check_theorem_5_3_strategyproof,
    check_theorem_5_4_condition,
)


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
    witness: ManipulationWitness | None = None
    violations: List[OddPathViolation] = field(default_factory=list)
    sp_despite_failure_reason: str | None = None


@dataclass
class ProbabilityBucketSummary:
    """
    Aggregated experimental results for a single attack probability p.
    """

    p: float
    total_instances: int
    strategyproof_count: int
    theorem_5_4_holds_count: int
    t54_holds_but_not_sp_count: int
    sp_although_t54_fails_count: int
    both_fail_count: int
    t54_holds_but_not_sp_examples: List[InstanceRecord]
    sp_although_t54_fails_examples: List[InstanceRecord]
    not_sp_examples: List[InstanceRecord]
    reason_breakdown: Dict[str, int]

    @property
    def strategyproof_fraction(self) -> float:
        return self.strategyproof_count / self.total_instances if self.total_instances else 0.0

    @property
    def theorem_5_4_holds_fraction(self) -> float:
        return self.theorem_5_4_holds_count / self.total_instances if self.total_instances else 0.0


def generate_random_instance(
    rng: random.Random,
    p: float,
    instance_id: int = 0,
    min_args: int = 6,
    max_args: int = 8,
    allow_self_attacks: bool = False,
) -> Tuple[ArgumentationFramework, Dict[str, Set[str]]]:
    """
    Generate a single random instance with:
      - `n` chosen uniformly from `{6, 7, 8}`
      - Arguments `a1, ..., an` partitioned uniformly at random among 3 agents (`Agent_1`, `Agent_2`, `Agent_3`)
      - Each possible directed attack `(au, av)` included independently with probability `p`.
        (By default `allow_self_attacks=False` generates attacks among distinct arguments `au != av`;
        if `allow_self_attacks=True`, self-loops `au -> au` are also sampled with probability `p`.)
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

    # Split arguments at random among 3 agents
    agent_types: Dict[str, Set[str]] = {
        "Agent_1": set(),
        "Agent_2": set(),
        "Agent_3": set(),
    }
    agent_names = ["Agent_1", "Agent_2", "Agent_3"]
    for arg in args:
        chosen_agent = rng.choice(agent_names)
        agent_types[chosen_agent].add(arg)

    return af, agent_types


def classify_why_strategyproof_despite_t54_failure(
    af: ArgumentationFramework,
    agent_types: Dict[str, Set[str]],
    violations: List[OddPathViolation],
) -> str:
    """
    Analyze structurally why an instance is strategyproof (Theorem 5.3 holds)
    even though Theorem 5.4's condition fails (an agent has an odd-length path
    between its own arguments).

    Categories:
    1. "Odd Self-Cycle Only (alpha == beta)":
       All odd-length paths within A_i start and end at the same argument
       (alpha -> ... -> alpha). Since hiding alpha removes alpha itself from
       the revealed graph, it can never rescue alpha or improve utility.
    2. "Direct Internal Conflict Only (Length-1 Swap / Defeated Attacker)":
       All distinct-argument odd paths within A_i have length 1 (alpha -> beta).
       Whenever alpha blocks beta, either alpha is itself accepted (so hiding
       alpha loses alpha [-1] to gain at most beta [+1], net change <= 0) or
       alpha is defeated / beta is independently blocked.
    3. "Indirect Odd Path Neutralized or 1-for-1 Bounded (Example 5.11 Type)":
       An indirect odd-length path (length >= 3, e.g. alpha -> gamma -> delta -> beta)
       exists between distinct arguments in A_i, but either intermediate attackers
       are defeated by other arguments (cancelling the indirect self-defeat, as in
       Example 5.11 where a6 -> a3) or hiding alpha trades at most 1 accepted
       argument for 1 rescued argument (net utility change <= 0).
    """
    distinct_violations = [v for v in violations if v.source != v.target]
    if not distinct_violations:
        return "Odd Self-Cycle Only (alpha == beta: hiding alpha removes it, so it cannot rescue another argument in A_i)"

    has_indirect_odd = any(v.length >= 3 for v in distinct_violations)
    if not has_indirect_odd:
        return "Direct Internal Conflict Only (Length-1 Swap / Neutralized: losing accepted alpha gains at most beta, net gain <= 0)"

    return "Indirect Odd Path Cancelled or 1-for-1 Bounded (Example 5.11 Type: intermediate attacker defeated or hiding alpha swaps <=1 for <=1)"


def run_experiments(
    num_instances_per_p: int = 1000,
    probabilities: Tuple[float, ...] = (0.15, 0.25, 0.35),
    seed: int = 42,
    allow_self_attacks: bool = False,
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
        t54_holds_not_sp = 0
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
            )

            t53_res = check_theorem_5_3_strategyproof(af, agent_types)
            t54_res = check_theorem_5_4_condition(
                af, agent_types, allow_walks=True, distinct_only=False
            )
            t54_distinct_res = check_theorem_5_4_condition(
                af, agent_types, allow_walks=True, distinct_only=True
            )

            is_sp = t53_res.is_strategyproof
            t54_holds = t54_res.condition_holds

            reason: str | None = None
            if is_sp and not t54_holds:
                reason = classify_why_strategyproof_despite_t54_failure(
                    af, agent_types, t54_res.violations
                )
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

            record = InstanceRecord(
                instance_id=global_id,
                p=p,
                num_args=len(af.arguments),
                af=af,
                agent_types=agent_types,
                is_strategyproof=is_sp,
                theorem_5_4_holds=t54_holds,
                theorem_5_4_distinct_holds=t54_distinct_res.condition_holds,
                witness=t53_res.witness,
                violations=t54_res.violations,
                sp_despite_failure_reason=reason,
            )

            if is_sp:
                sp_count += 1
            if t54_holds:
                t54_count += 1

            if t54_holds and not is_sp:
                t54_holds_not_sp += 1
                if len(t54_holds_not_sp_examples) < 5:
                    t54_holds_not_sp_examples.append(record)
            elif is_sp and not t54_holds:
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
            t54_holds_but_not_sp_count=t54_holds_not_sp,
            sp_although_t54_fails_count=sp_but_t54_fails,
            both_fail_count=both_fail,
            t54_holds_but_not_sp_examples=t54_holds_not_sp_examples,
            sp_although_t54_fails_examples=sp_but_t54_fails_examples,
            not_sp_examples=not_sp_examples,
            reason_breakdown=reason_counts,
        )

    return summaries
