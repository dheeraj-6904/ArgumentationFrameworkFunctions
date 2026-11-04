# Argumentation Engine & Strategic Argumentation

A modular, SOLID-compliant Python implementation of Dung's **Abstract Argumentation Framework** ($\langle A, \rightharpoonup \rangle$), Caminada's **Three-Valued Argument Labellings** ($\{\text{in}, \text{out}, \text{undec}\}$), and Rahwan & Larson's **Grounded Direct Argumentation Mechanism** ($\mathcal{M}_{AF}^{grnd}$) for multi-agent strategic argumentation analysis, based on Chapter 5 (*"Argumentation among Agents"* by Iyad Rahwan) of *Multiagent Systems* (2nd ed., edited by Gerhard Weiss, MIT Press).

---

## Project Structure

```text
ArgumentationFrameworkFunctions/
├── src/
│   ├── __init__.py          # Top-level package exports for all required functions & classes
│   ├── framework.py         # Part 1 (Items 1-4): ArgumentationFramework <A, -> >, conflict-free,
│   │                        #   defense check, and characteristic function F_AF(S)
│   ├── semantics.py         # Part 1 (Items 5, 6A-C, 6E): Admissibility, Complete, Grounded,
│   │                        #   Preferred, Stable, Semi-Stable extensions & acceptance status
│   ├── labelling.py         # Part 1 (Item 6D): Legal (in/out/undec) labellings & validation
│   ├── strategic.py         # Part 2 (Items 1-4): Grounded Direct Argumentation Mechanism,
│   │                        #   subset utility maximization, Theorem 5.3 & Theorem 5.4 (cycle-safe)
│   ├── book_examples.py     # Reproduction & verification of Chapter 5 book examples + misprints
│   └── experiments.py       # Monte Carlo random instance generator & statistical analyzer
├── tests/
│   ├── conftest.py
│   ├── test_framework.py
│   ├── test_semantics_and_labelling.py
│   ├── test_strategic.py
│   └── test_experiments_and_examples.py
├── demo.py                  # Full end-to-end CLI demonstration (Book Examples + 3,000 Experiments)
├── REPORT.md                # Comprehensive technical & experimental report
├── README.md                # Project documentation and usage guide
└── LICENSE
```

*(Note: Architectural and algorithmic decision logs are maintained in `docs/key_decisions.md`, which is git-ignored per project specification.)*

---

## Mapping of Assignment Requirements to Code

### Part 1: Argumentation Engine
1. **Framework Class $\langle A, \rightharpoonup \rangle$**: [`ArgumentationFramework`](src/framework.py)
2. **Conflict-Free Test**: [`is_conflict_free(af, S)`](src/framework.py)
3. **Argument Defense Test**: [`is_defended_by(af, alpha, S)`](src/framework.py)
4. **Characteristic Function $F_{AF}(S)$**: [`characteristic_function(af, S)`](src/framework.py)
5. **Admissibility & Complete Extension Check**: [`is_admissible(af, S)`](src/semantics.py), [`is_complete_extension(af, S)`](src/semantics.py), and [`check_admissible_and_complete(af, S)`](src/semantics.py)
6. **Extension & Labelling Evaluators**:
   - **(A) Grounded Extension**: [`compute_grounded_extension(af)`](src/semantics.py)
   - **(B) All Complete Extensions**: [`compute_complete_extensions(af)`](src/semantics.py)
   - **(C) Preferred, Stable, and Semi-Stable Extensions**: [`compute_preferred_extensions(af)`](src/semantics.py), [`compute_stable_extensions(af)`](src/semantics.py), [`compute_semi_stable_extensions(af)`](src/semantics.py), and [`compute_all_extensions(af)`](src/semantics.py)
   - **(D) All Legal (`in`/`out`/`undec`) Labellings**: [`generate_legal_labellings(af)`](src/labelling.py)
   - **(E) Argument Acceptance Status (`skeptically accepted` / `credulously accepted` / `rejected`)**: [`report_acceptance_status(af, alpha, semantics="preferred")`](src/semantics.py)

### Part 2: Strategic Argumentation & Experiments
1. **Grounded Direct Argumentation Mechanism**: [`grounded_direct_mechanism(global_af, revealed_reports)`](src/strategic.py)
2. **Subset Enumeration & Best-Response Utility Maximization**: [`find_best_responses(global_af, agent_id, agent_true_args, other_agents_reports)`](src/strategic.py)
3. **Theorem 5.3 Verification (Exact Strategyproofness)**: [`check_theorem_5_3_strategyproof(global_af, agent_types)`](src/strategic.py)
4. **Theorem 5.4 Verification (No Odd-Length Directed Path/Walk with Cycle Handling)**: [`check_theorem_5_4_condition(global_af, agent_types, allow_walks=True, distinct_only=False)`](src/strategic.py) (along with [`has_odd_path_naive_visited`](src/strategic.py) demonstrating why single-visited-set BFS fails on cyclic/reconvergent graphs)
5. **Random Instance Generator & Verified Outcome Analyzer**: [`generate_random_instance(rng, p, allow_self_attacks=True, require_non_empty_agents=True)`](src/experiments.py) and [`verify_why_strategyproof_despite_t54_failure(af, agent_types, violations)`](src/experiments.py)

---

## Installation & Quick Start

The codebase uses pure Python 3.10+ standard library modules for all core algorithms and `pytest` for unit testing.

### 1. Run the Full Demonstration (Book Examples + 3,000 Random Instances)
```bash
python demo.py
```
You can also customize the number of random instances per probability $p \in \{0.15, 0.25, 0.35\}$ and the random seed:
```bash
python demo.py --instances-per-p 1000 --seed 42
```

### 2. Run the Unit Test Suite
```bash
pytest -v
```

### 3. Programmatic Usage Example
```python
from src import (
    ArgumentationFramework,
    compute_all_extensions,
    generate_legal_labellings,
    report_acceptance_status,
    grounded_direct_mechanism,
    find_best_responses,
    check_theorem_5_3_strategyproof,
    check_theorem_5_4_condition,
)

# 1. Build Figure 5.2 from the textbook
af = ArgumentationFramework(
    arguments=["a1", "a2", "a3"],
    attacks=[("a1", "a2"), ("a2", "a1")],
)

print("All Extensions:", compute_all_extensions(af))
print("Legal Labellings:", generate_legal_labellings(af))
print("Status of a1:", report_acceptance_status(af, "a1"))
print("Status of a3:", report_acceptance_status(af, "a3"))

# 2. Strategic Argumentation (Example 5.10)
af_5_10 = ArgumentationFramework(
    arguments=["a1", "a2", "a3", "a4", "a5"],
    attacks=[("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")],
)
types = {"x": {"a1", "a4", "a5"}, "y": {"a2"}, "z": {"a3"}}

print("Truthful Outcome:", grounded_direct_mechanism(af_5_10, types))
br_x = find_best_responses(af_5_10, "x", types["x"], {"y": types["y"], "z": types["z"]})
print("Agent x Best Reports:", br_x.best_reports, "Max Utility:", br_x.max_utility)
print("Satisfies Theorem 5.3?", check_theorem_5_3_strategyproof(af_5_10, types).is_strategyproof)
print("Satisfies Theorem 5.4?", check_theorem_5_4_condition(af_5_10, types).condition_holds)
```
