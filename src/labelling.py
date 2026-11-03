"""
src/labelling.py

Caminada's Three-Valued Argument Labelling Engine (Part 1: Item 6D).

In Rahwan Ch. 5 (Section 5.3.2, Alternative Formulation: Argument Labeling),
a labelling is a total mapping L : A -> {in, out, undec}.
A labelling L is a legal (complete) labelling iff for every alpha in A:
  1. L(alpha) == "in"    <=> for all beta -> alpha, L(beta) == "out"
  2. L(alpha) == "out"   <=> exists beta -> alpha such that L(beta) == "in"
  3. L(alpha) == "undec" <=> not all beta -> alpha have L(beta) == "out",
                             and no beta -> alpha has L(beta) == "in".
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, Iterator, List, Mapping, Set

from src.framework import ArgumentationFramework
from src.semantics import compute_complete_extensions

IN = "in"
OUT = "out"
UNDEC = "undec"
VALID_LABELS = frozenset({IN, OUT, UNDEC})


@dataclass(frozen=True)
class ArgumentLabelling(Mapping[str, str]):
    """
    Immutable representation of an argument labelling L : A -> {in, out, undec}.
    Implements the standard Python `Mapping` interface so it can be indexed
    like a dictionary (`L["a1"] == "in"`) while also providing `.in_set`,
    `.out_set`, and `.undec_set` properties.
    """

    labels: Dict[str, str]

    def __init__(self, labels: Mapping[str, str]) -> None:
        cleaned: Dict[str, str] = {}
        for arg, lbl in sorted(labels.items()):
            if lbl not in VALID_LABELS:
                raise ValueError(
                    f"Invalid label '{lbl}' for argument '{arg}'. Must be one of {sorted(VALID_LABELS)}."
                )
            cleaned[arg] = lbl
        object.__setattr__(self, "labels", cleaned)

    def __getitem__(self, key: str) -> str:
        return self.labels[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.labels)

    def __len__(self) -> int:
        return len(self.labels)

    @property
    def in_set(self) -> FrozenSet[str]:
        """Return { alpha in A | L(alpha) == 'in' }."""
        return frozenset(a for a, lbl in self.labels.items() if lbl == IN)

    @property
    def out_set(self) -> FrozenSet[str]:
        """Return { alpha in A | L(alpha) == 'out' }."""
        return frozenset(a for a, lbl in self.labels.items() if lbl == OUT)

    @property
    def undec_set(self) -> FrozenSet[str]:
        """Return { alpha in A | L(alpha) == 'undec' }."""
        return frozenset(a for a, lbl in self.labels.items() if lbl == UNDEC)

    def to_dict(self) -> Dict[str, str]:
        """Return a standard dictionary copy of the labelling."""
        return dict(self.labels)

    def __repr__(self) -> str:
        in_str = "{" + ", ".join(sorted(self.in_set)) + "}"
        out_str = "{" + ", ".join(sorted(self.out_set)) + "}"
        undec_str = "{" + ", ".join(sorted(self.undec_set)) + "}"
        return f"Labelling(in={in_str}, out={out_str}, undec={undec_str})"


def is_legal_labelling(
    af: ArgumentationFramework, labelling: Mapping[str, str]
) -> bool:
    """
    Verify directly from the three Caminada / Rahwan labelling axioms whether
    `labelling` is a legal (complete) in/out/undec labelling of `af`.
    """
    if set(labelling.keys()) != set(af.arguments):
        return False

    for alpha in af.arguments:
        lbl = labelling[alpha]
        if lbl not in VALID_LABELS:
            return False

        attackers = af.attackers_of(alpha)
        all_attackers_out = all(labelling[beta] == OUT for beta in attackers)
        some_attacker_in = any(labelling[beta] == IN for beta in attackers)

        if lbl == IN and not all_attackers_out:
            return False
        if lbl == OUT and not some_attacker_in:
            return False
        if lbl == UNDEC and (all_attackers_out or some_attacker_in):
            return False

    return True


def extension_to_labelling(
    af: ArgumentationFramework, ext: Iterable[str]
) -> ArgumentLabelling:
    """
    Convert a complete extension E into its corresponding legal labelling L_E:
      - in(L_E)    = E
      - out(L_E)   = E^+ (arguments defeated by E)
      - undec(L_E) = A \\ (E cup E^+)
    """
    ext_set: Set[str] = af._validate_subset(ext)
    ext_plus = af.set_attacked_by(ext_set)

    mapping: Dict[str, str] = {}
    for alpha in af.ordered_arguments:
        if alpha in ext_set:
            mapping[alpha] = IN
        elif alpha in ext_plus:
            mapping[alpha] = OUT
        else:
            mapping[alpha] = UNDEC
    return ArgumentLabelling(mapping)


def generate_legal_labellings(
    af: ArgumentationFramework,
) -> List[ArgumentLabelling]:
    """
    Item 6(D): Generate all legal (in/out/undec) labellings of a given
    argumentation framework.

    Theorem (Caminada 2006 / Rahwan Ch. 5):
    There is a bijection between the complete extensions of AF and the legal
    (complete) labellings of AF:
      - Each complete extension E induces L_E with in=E, out=E^+, undec=A\\(E cup E^+).
      - Each legal labelling L satisfies that in(L) is a complete extension.
    We construct each legal labelling and assert `is_legal_labelling` to
    guarantee the three local labelling conditions hold on every node.
    """
    complete_exts = compute_complete_extensions(af)
    labellings: List[ArgumentLabelling] = []
    for ext in complete_exts:
        lbl = extension_to_labelling(af, ext)
        assert is_legal_labelling(af, lbl), f"Generated illegal labelling: {lbl}"
        labellings.append(lbl)
    return labellings
