# Assignment 3 Technical Report: Argumentation Engine & Strategic Argumentation

---

## 1. Executive Summary

This report presents the design, theoretical verification, and experimental evaluation of:
1. **Part 1 — Abstract Argumentation Engine**: A full implementation of Dung's abstract argumentation framework $\langle A, \rightharpoonup \rangle$, conflict-freeness, argument defense, the characteristic function $F_{AF}(S)$, admissibility, extension-based semantics (**grounded**, **complete**, **preferred**, **stable**, and **semi-stable**), Caminada's **legal (`in`/`out`/`undec`) labellings**, and argument acceptance status (**skeptically accepted**, **credulously accepted**, **rejected**).
2. **Part 2 — Strategic Argumentation (Grounded Direct Argumentation Mechanism)**: An implementation of the multi-agent mechanism $\mathcal{M}_{AF}^{grnd}$, optimal subset revelation (best-response search), exact strategyproofness verification (**Theorem 5.3**), and cycle-aware odd-length directed path/walk verification (**Theorem 5.4**).
3. **Part 3 — Monte Carlo Experiments**: A statistical and game-theoretic investigation across **3,000 random instances** (1,000 instances for each attack probability $p \in \{0.15, 0.25, 0.35\}$, with $n \in \{6, 7, 8\}$ arguments partitioned among 3 agents), complete with exhaustive grounded-outcome deviation verification and an ablation appendix comparing generator and path/walk design choices.

---

## 2. Part 1: Argumentation Engine & Book Example Verification

### 2.1 Architecture & Algorithmic Summary
- **Dual-Adjacency Graph Representation ([`src/framework.py`](src/framework.py))**: `ArgumentationFramework` pre-indexes incoming attackers ($\{\beta \in A \mid \beta \rightharpoonup \alpha\}$) and outgoing targets ($\{\beta \in A \mid \alpha \rightharpoonup \beta\}$) for each argument. Consequently, computing the defeated range $S^+ = \{\beta \in A \mid \exists \gamma \in S, \gamma \rightharpoonup \beta\}$ and testing defense ($\text{attackers}(\alpha) \subseteq S^+$) execute in $O(|S|)$ set operations.
- **Grounded Extension ([`src/semantics.py`](src/semantics.py))**: Computed in polynomial time $O(|A|^3)$ as the least fixed point of the monotonic characteristic function $F_{AF}(S) = \{\alpha \in A \mid \text{attackers}(\alpha) \subseteq S^+\}$, iterating $S_{k+1} = F_{AF}(S_k)$ from $S_0 = \emptyset$ until convergence.
- **Complete, Preferred, Stable, and Semi-Stable Extensions ([`src/semantics.py`](src/semantics.py))**:
  - Every complete extension $E$ satisfies $E_{grnd} \subseteq E \subseteq A \setminus (E_{grnd} \cup E_{grnd}^+)$. We seed a pruned backtracking search with $E_{grnd}$, immediately pruning any branch that introduces an internal conflict or self-attack, and collect fixed points satisfying $F_{AF}(E) = E$.
  - **Preferred extensions** are extracted as the $\subseteq$-maximal complete extensions.
  - **Stable extensions** are extracted as complete extensions satisfying $E \cup E^+ = A$.
  - **Semi-stable extensions** are extracted as complete extensions whose range $E \cup E^+$ is $\subseteq$-maximal among all complete extensions.
- **Legal Labellings ([`src/labelling.py`](src/labelling.py))**: Each complete extension $E$ maps bijectively to a legal labelling $\mathcal{L}_E$ with $\text{in}(\mathcal{L}_E) = E$, $\text{out}(\mathcal{L}_E) = E^+$, and $\text{undec}(\mathcal{L}_E) = A \setminus (E \cup E^+)$, verified directly against Caminada's three local legality conditions.

### 2.2 Verification on Textbook Examples (Chapter 5, Rahwan)

#### Figure 5.1 (Examples 5.5, 5.6, 5.8)
- **Framework**: $A = \{\alpha_1, \alpha_2, \alpha_3, \alpha_4, \alpha_5\}$, attacks $\rightharpoonup = \{(\alpha_3, \alpha_2), (\alpha_2, \alpha_1), (\alpha_5, \alpha_4), (\alpha_4, \alpha_1)\}$.
- **Defense & Characteristic Function**:
  - $\{\alpha_3, \alpha_5\}$ is conflict-free and defends $\alpha_1$ (since $\alpha_3$ defeats $\alpha_2$ and $\alpha_5$ defeats $\alpha_4$), whereas $\{\alpha_3\}$ alone does not defend $\alpha_1$.
  - $F_{AF}(\emptyset) = \{\alpha_3, \alpha_5\}$, $F_{AF}(\{\alpha_3, \alpha_5\}) = \{\alpha_1, \alpha_3, \alpha_5\}$, and $F_{AF}(\{\alpha_1, \alpha_3, \alpha_5\}) = \{\alpha_1, \alpha_3, \alpha_5\}$.
- **Admissibility vs. Completeness**:
  - $\emptyset, \{\alpha_3\}, \{\alpha_5\}, \{\alpha_3, \alpha_5\}$ are **admissible** ($S \subseteq F_{AF}(S)$) but **not complete** ($S \neq F_{AF}(S)$).
  - $\{\alpha_1, \alpha_3, \alpha_5\}$ is the **unique complete, grounded, preferred, stable, and semi-stable extension**.
- **Legal Labelling & Acceptance Status**:
  - Unique legal labelling: $\text{in} = \{\alpha_1, \alpha_3, \alpha_5\}$, $\text{out} = \{\alpha_2, \alpha_4\}$, $\text{undec} = \emptyset$.
  - Acceptance status: $\alpha_1, \alpha_3, \alpha_5$ are **skeptically accepted**; $\alpha_2, \alpha_4$ are **rejected**.

#### Figure 5.2 (Examples 5.7, 5.8)
- **Framework**: $A = \{\alpha_1, \alpha_2, \alpha_3\}$, attacks $\rightharpoonup = \{(\alpha_1, \alpha_2), (\alpha_2, \alpha_1)\}$.
- **Extensions**:
  - **Grounded Extension**: $\{\alpha_3\}$
  - **Complete Extensions**: $\{\alpha_3\}$, $\{\alpha_1, \alpha_3\}$, $\{\alpha_2, \alpha_3\}$
  - **Preferred / Stable / Semi-Stable Extensions**: $\{\alpha_1, \alpha_3\}$, $\{\alpha_2, \alpha_3\}$
- **Legal Labellings ($L_G, L_1, L_2$)**:
  - $L_G$: $\text{in} = \{\alpha_3\}, \text{out} = \emptyset, \text{undec} = \{\alpha_1, \alpha_2\}$
  - $L_1$: $\text{in} = \{\alpha_1, \alpha_3\}, \text{out} = \{\alpha_2\}, \text{undec} = \emptyset$
  - $L_2$: $\text{in} = \{\alpha_2, \alpha_3\}, \text{out} = \{\alpha_1\}, \text{undec} = \emptyset$
- **Acceptance Status (under Preferred/Complete semantics)**:
  - $\alpha_3$: **skeptically accepted**
  - $\alpha_1, \alpha_2$: **credulously accepted** (and **rejected** under Grounded semantics).

---

## 3. Part 2: Strategic Argumentation & Textbook Misprints

### 3.1 Example 5.10 (Beneficial Hiding of Arguments & Misprint #1)
- **Setup**: Three agents $x, y, z$ with private argument sets $A_x = \{\alpha_1, \alpha_4, \alpha_5\}$, $A_y = \{\alpha_2\}$, $A_z = \{\alpha_3\}$ and global defeat relation $R = \{(\alpha_1, \alpha_2), (\alpha_2, \alpha_3), (\alpha_3, \alpha_4), (\alpha_3, \alpha_5)\}$.
- **Truthful Revelation Outcome**:
  - When all agents report truthfully, $E_{grnd}(A) = \{\alpha_1, \alpha_3\}$.
  - True utilities:
    $$u_x = |\{\alpha_1, \alpha_4, \alpha_5\} \cap \{\alpha_1, \alpha_3\}| = 1, \quad u_y = |\{\alpha_2\} \cap \{\alpha_1, \alpha_3\}| = 0, \quad u_z = |\{\alpha_3\} \cap \{\alpha_1, \alpha_3\}| = 1.$$
  - **Textbook Misprint #1**: In the book, the utilities of $y$ and $z$ are written with each other's argument sets ($u_y(o, \{\alpha_3\}) = 1$ and $u_z(o, \{\alpha_2\}) = 0$). Using their actual sets $A_y = \{\alpha_2\}$ and $A_z = \{\alpha_3\}$, their utilities are $u_y = 0$ and $u_z = 1$.
- **Strategic Manipulation by Agent $x$**:
  - Enumerating all $2^3 = 8$ subsets of $A_x$ against $A_y^\circ = \{\alpha_2\}, A_z^\circ = \{\alpha_3\}$ shows that when agent $x$ hides $\alpha_1$ and reveals $A_x^\circ = \{\alpha_4, \alpha_5\}$, $\alpha_2$ is no longer defeated by $\alpha_1$, so $\alpha_2$ defeats $\alpha_3$, which defends both $\alpha_4$ and $\alpha_5$!
  - The induced grounded extension becomes $E_{grnd}(\{\alpha_2, \alpha_3, \alpha_4, \alpha_5\}) = \{\alpha_2, \alpha_4, \alpha_5\}$, increasing agent $x$'s utility from $u_x = 1$ to $u_x = 2$.
  - Both **Theorem 5.3** (`is_strategyproof = False`) and **Theorem 5.4** (`condition_holds = False`, due to length-3 odd paths $\alpha_1 \rightharpoonup \alpha_2 \rightharpoonup \alpha_3 \rightharpoonup \alpha_4$ and $\alpha_1 \rightharpoonup \alpha_2 \rightharpoonup \alpha_3 \rightharpoonup \alpha_5$) evaluate to `False`.

### 3.2 Example 5.11 (Cancellation of Indirect Self-Defeat & Misprint #2)
- **Setup**: Adds argument $\alpha_6$ to $A_x$ ($A_x = \{\alpha_1, \alpha_4, \alpha_5, \alpha_6\}$) with attack $(\alpha_6, \alpha_3)$.
- **Verification**:
  - Under truthful revelation, $\alpha_6$ is unattacked and directly defeats $\alpha_3$, yielding $E_{grnd}(A) = \{\alpha_1, \alpha_4, \alpha_5, \alpha_6\}$ and maximal possible utility $u_x = 4$.
  - **Theorem 5.3** evaluates to `True` (truth-telling is a dominant strategy for every agent against every opponent report profile), whereas **Theorem 5.4** evaluates to `False` (the odd-length paths $\alpha_1 \rightharpoonup \alpha_2 \rightharpoonup \alpha_3 \rightharpoonup \alpha_4$ and $\alpha_1 \rightharpoonup \alpha_2 \rightharpoonup \alpha_3 \rightharpoonup \alpha_5$ still exist in the graph).
  - **Textbook Misprint #2**: In the textbook's discussion after Example 5.11, the text states that $\alpha_5$ cancels the indirect self-defeat; in fact, it is **$\alpha_6$** (via the attack $\alpha_6 \rightharpoonup \alpha_3$) that neutralizes $\alpha_3$ and cancels the indirect self-defeat.

### 3.3 Formulation of Theorem 5.4 & Dealing with Cycles
In Rahwan Chapter 5 (Theorem 5.4), the sufficient condition states that each agent's type $A_i$ is a conflict-free set of arguments containing no (in)direct defeats ($\nexists \alpha_1, \alpha_2 \in A_i$ with an odd-length directed path from $\alpha_1$ to $\alpha_2$ in the full graph):
1. **Why Cycle-Aware Parity Search is Essential (Demonstrated in `demo.py` Case C & `tests/test_strategic.py`)**:
   A naive graph traversal (`has_odd_path_naive_visited` in [`src/strategic.py`](src/strategic.py)) that maintains a single global `visited` set of vertices fails when an even-length path and an odd-length path reconverge at an intermediate vertex or cycle.
   - **Concrete Counterexample Verified in Code**: Consider $A = \{a_1, a_2, a_3, a_4, a_5, b_1, b_2, c\}$ with $A_x = \{a_1, a_4, a_5\}$, $A_y = \{b_1, a_2\}$, $A_z = \{b_2, c, a_3\}$, and attacks $R = \{a_1 \rightharpoonup c, c \rightharpoonup a_2, a_2 \rightharpoonup c, a_1 \rightharpoonup b_1, b_1 \rightharpoonup b_2, b_2 \rightharpoonup a_2, a_2 \rightharpoonup a_3, a_3 \rightharpoonup a_4, a_3 \rightharpoonup a_5\}$ (note the 2-cycle $c \leftrightarrow a_2$).
   - From $a_1$ to $a_4, a_5$, there is an **even path of length 4** ($a_1 \rightharpoonup c \rightharpoonup a_2 \rightharpoonup a_3 \rightharpoonup a_4$) that reaches $a_2$ at distance 2 (even), and an **odd path of length 5** ($a_1 \rightharpoonup b_1 \rightharpoonup b_2 \rightharpoonup a_2 \rightharpoonup a_3 \rightharpoonup a_4$) that reaches $a_2$ at distance 3 (odd).
   - Because `has_odd_path_naive_visited` marks $a_2$ visited at distance 2, it ignores $b_2 \rightharpoonup a_2$ at distance 3 and **falsely claims Theorem 5.4 holds** (`naive_any_odd = False`), even though **Theorem 5.3 fails** (when Agent $y$ reveals $\{b_1, a_2\}$ and Agent $z$ reveals $\{b_2, a_3\}$, Agent $x$ increases utility from $1$ to $2$ by hiding $a_1$)!
   - To handle cycles and reconvergent paths rigorously, [`src/strategic.py`](src/strategic.py) implements both branch-local backtracking (`find_odd_length_simple_path`) and parity-state BFS (`find_odd_length_walk`) on $A \times \{0, 1\}$.
2. **Design Variations Explicitly Tracked**:
   - **All pairs $(\alpha, \beta) \in A_i \times A_i$ (`distinct_only=False`, Primary) vs. Distinct pairs $\alpha \neq \beta$ (`distinct_only=True`)**: Including $\alpha = \beta$ enforces that no $\alpha \in A_i$ has a self-attack $\alpha \rightharpoonup \alpha$ (length 1) or odd cycle to itself. Both variants are computed and reported in Section 4.
   - **Odd directed walks (`allow_walks=True`, Primary) vs. Simple odd paths (`allow_walks=False`)**: When a graph contains a self-loop or odd cycle along an even simple path (e.g., $a_1 \rightharpoonup a_2 \rightharpoonup a_2 \rightharpoonup a_6$ of length 3), traversing the cycle yields an odd-length walk with repeated vertices even when no simple odd path exists. Both variants are tracked and explicitly labeled.

---

## 4. Part 3: Experimental Results & Analysis

### 4.1 Experimental Setup & Design Choices
- **Agents**: 3 agents (`Agent_1`, `Agent_2`, `Agent_3`).
- **Arguments & Non-Empty Partition (`require_non_empty_agents=True`)**: For each instance, $n \in \{6, 7, 8\}$ is chosen uniformly at random. To guarantee all 3 agents participate with non-empty private sets ($A_i \neq \emptyset$), the $n$ arguments are randomly shuffled, the first 3 arguments are assigned one to each agent, and the remaining $n - 3$ arguments are distributed uniformly at random among the 3 agents.
- **Full $n^2$ Directed Attack Sampling (`allow_self_attacks=True`)**: Every ordered pair $(\alpha_u, \alpha_v) \in A \times A$ (all $n^2$ possible directed attacks, including self-attacks $u = v$) is included independently with probability $p \in \{0.15, 0.25, 0.35\}$.
- **Sample Size**: **1,000 random instances per $p$** (**3,000 instances total**, `seed=42`).
*(Note: Section 4.4 provides a full sensitivity comparison across all 4 combinations of `allow_self_attacks` $\in \{\text{True}, \text{False}\}$ and `require_non_empty_agents` $\in \{\text{True}, \text{False}\}$).*

### 4.2 Primary Summary Table (Questions 1, 2, and 3)

| Attack Prob $p$ | Total Instances | Strategyproof (Theorem 5.3 Holds) | Fraction Strategyproof (Q1) | Thm 5.4 Holds (All Pairs $\alpha, \beta \in A_i$) | Thm 5.4 Holds (Distinct $\alpha \neq \beta$) | Thm 5.4 Holds & Fails SP (Q2) | Strategyproof Despite Thm 5.4 Failing (Q3) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$0.15$** | $1000$ | $581$ | **$0.5810$ ($58.1\%$)** | $52$ ($5.2\%$) | $137$ ($13.7\%$) | **$0$ ($0.0\%$)** | $529$ ($52.9\%$) |
| **$0.25$** | $1000$ | $235$ | **$0.2350$ ($23.5\%$)** | $4$ ($0.4\%$) | $11$ ($1.1\%$) | **$0$ ($0.0\%$)** | $231$ ($23.1\%$) |
| **$0.35$** | $1000$ | $158$ | **$0.1580$ ($15.8\%$)** | $2$ ($0.2\%$) | $5$ ($0.5\%$) | **$0$ ($0.0\%$)** | $156$ ($15.6\%$) |
| **Total** | **$3000$** | **$974$** | **$0.3247$ ($32.5\%$)** | **$58$ ($1.9\%$)** | **$153$ ($5.1\%$)** | **$0$ ($0.0\%$)** | **$916$ ($30.5\%$)** |

---

### 4.3 Detailed Answers to Experimental Questions

#### Question 1: Fraction of Instances that are Strategyproof for Each $p$
- For **$p = 0.15$**: **$0.5810$ ($58.1\%$)** of instances ($581 / 1000$) are strategyproof.
- For **$p = 0.25$**: **$0.2350$ ($23.5\%$)** of instances ($235 / 1000$) are strategyproof.
- For **$p = 0.35$**: **$0.1580$ ($15.8\%$)** of instances ($158 / 1000$) are strategyproof.
- **Explanation of Trend**: As attack probability $p$ increases from $0.15$ to $0.35$, the expected number of directed attacks grows from $0.15 n^2$ to $0.35 n^2$, sharply increasing the density of internal conflicts and odd-length indirect defeat paths within each agent's argument set. This gives agents more opportunities to profitably withhold an argument that either triggers an odd-length self-defeat chain or locks a defender in a cycle.

---

#### Question 2: How Many Instances Satisfy the Condition in Theorem 5.4 Yet Fail Strategyproofness?
- **Result**: **$0$ instances out of $3,000$** satisfy Theorem 5.4's condition yet fail strategyproofness. This holds identically whether Theorem 5.4 is evaluated over:
  - All pairs $\alpha, \beta \in A_i$ with odd walks allowed (`0 / 3,000`),
  - Distinct pairs $\alpha \neq \beta \in A_i$ with odd walks allowed (`0 / 3,000`), or
  - Simple odd paths only (`0 / 3,000`).
- **Mathematical Explanation**:
  Theorem 5.4 is a mathematically proven **sufficient condition** ($\text{Theorem 5.4 Condition} \implies \text{Strategyproofness}$). By induction on the iterations $S_{k+1} = F_{AF}(S_k)$ of the characteristic function, when agent $i$ reveals an additional argument $\alpha \in A_i$ on top of $S \subseteq A_i$:
  1. Any argument $x \in E_{grnd}(S \cup A_{-i}^\circ) \setminus E_{grnd}((S \cup \{\alpha\}) \cup A_{-i}^\circ)$ that loses acceptance when $\alpha$ is revealed must be reachable from $\alpha$ by an **odd-length directed path/walk** ($\alpha \rightharpoonup^{2m+1} x$).
  2. Any argument $y$ whose defeat is lost when $\alpha$ is revealed must be reachable from $\alpha$ by an **even-length directed path/walk** ($\alpha \rightharpoonup^{2m} y$).
  Furthermore, taking the minimal grounded rank at which acceptance/defeat diverges guarantees a **simple odd-length path** from $\alpha$ to some $\beta \in A_i \setminus \{\alpha\}$. Thus, when no odd-length directed path exists between arguments in $A_i$, revealing $\alpha$ can never exclude any $\beta \in A_i$ from the grounded extension.
- **Diagnostic Note on Length-1 Conflicts**:
  In `src/experiments.py` (`only_len_1_not_sp_count`), we also explicitly measure how many non-strategyproof instances have **only length-1 direct attacks** ($\alpha \rightharpoonup \beta$) inside $A_i$ and no odd path of length $\ge 3$: there are **$93$** such instances at $p=0.15$, **$37$** at $p=0.25$, and **$11$** at $p=0.35$ ($141$ total). For example, if $\alpha \in A_i$ is self-attacking ($\alpha \rightharpoonup \alpha$) or locked in a cycle ($\alpha \notin E_{grnd}$) and directly attacks an otherwise unattacked $\beta \in A_i$ ($\alpha \rightharpoonup \beta$, length 1), revealing $\alpha$ destroys $\beta$'s acceptance while gaining nothing, so hiding $\alpha$ strictly increases utility. Because Theorem 5.4 requires $A_i$ to be conflict-free (excluding length-1 odd paths as well as length $\ge 3$ indirect odd paths), all $141$ cases are properly flagged as violating Theorem 5.4.

---

#### Question 3: Are There Instances that are Strategyproof Although Theorem 5.4's Condition Fails?
- **Result**: **Yes — $916$ out of $3,000$ instances ($30.5\%$)** are strategyproof even though Theorem 5.4's condition fails ($529$ at $p=0.15$, $231$ at $p=0.25$, $156$ at $p=0.35$).
- **Exact Game-Theoretic & Grounded-Outcome Verification (`verify_why_strategyproof_despite_t54_failure` in [`src/experiments.py`](src/experiments.py))**:
  Rather than guessing from path lengths, our analyzer exhaustively computes the truthful grounded outcome $E_{\text{truth}} = E_{grnd}(A_i \cup A_{-i}^\circ)$ and the deviating grounded outcome $E_{\text{dev}} = E_{grnd}(S \cup A_{-i}^\circ)$ across **every agent $i$**, **every opponent report profile $A_{-i}^\circ \subseteq A_{-i}$**, and **every subset $S \subseteq A_i$**, measuring:
  - **Rescued arguments**: $G(S, A_{-i}^\circ) = (A_i \cap E_{\text{dev}}) \setminus E_{\text{truth}}$ (arguments of $A_i$ not accepted under truthfulness that become accepted when $A_i \setminus S$ is hidden).
  - **Sacrificed arguments**: $L(S, A_{-i}^\circ) = (A_i \cap E_{\text{truth}}) \setminus E_{\text{dev}}$ (arguments of $A_i$ accepted under truthfulness that are lost when $A_i \setminus S$ is hidden).
  Since $u_i(S, A_{-i}^\circ) - u_i(A_i, A_{-i}^\circ) = |G(S, A_{-i}^\circ)| - |L(S, A_{-i}^\circ)|$, strategyproofness holds if and only if $|G(S, A_{-i}^\circ)| \le |L(S, A_{-i}^\circ)|$ in every profile (verified by assertion on all $916$ instances).

##### Mathematically Verified Breakdown of the 916 Instances

| Verified Grounded-Outcome Category | $p = 0.15$ | $p = 0.25$ | $p = 0.35$ | Total ($3,000$ runs) |
| :--- | :---: | :---: | :---: | :---: |
| **1A. Self-Attack / Odd Self-Cycle Only** ($\alpha = \beta$ only; verified $|G| = 0$ in all profiles) | $85$ | $7$ | $3$ | **$95$ ($10.4\%$)** |
| **1B. Path Cancelled / Target Accepted Under Truthfulness** (verified $|G| = 0$ in all profiles; Example 5.11 type) | $11$ | $6$ | $6$ | **$23$ ($2.5\%$)** |
| **1C. Target Unrescuable / Independently Blocked** (verified $|G| = 0$ in all profiles; target blocked even when source hidden) | $72$ | $92$ | $69$ | **$233$ ($25.4\%$)** |
| **2. Active Rescue Offset by Equal/Greater Sacrifice** (verified $|G| \ge 1$ in some profile, but $|L| \ge |G|$ in all profiles) | $361$ | $126$ | $78$ | **$565$ ($61.7\%$)** |
| **Total Strategyproof Despite Theorem 5.4 Failing** | **$529$** | **$231$** | **$156$** | **$916$ ($100\%$)** |

##### Concrete Noted Instances & Full Subset Deviation Proofs

1. **`[p = 0.15, Instance #2]` — Verified Category 2: Active Rescue Offset by Equal/Greater Sacrifice (`|G| = 1 <= |L|`)**
   - **Framework**: $A = \{a_1, a_2, a_3, a_4, a_5, a_6, a_7, a_8\}$, $R = \{a_1 \rightharpoonup a_4, a_1 \rightharpoonup a_5, a_2 \rightharpoonup a_5, a_4 \rightharpoonup a_4, a_5 \rightharpoonup a_3, a_6 \rightharpoonup a_1, a_7 \rightharpoonup a_5, a_8 \rightharpoonup a_4\}$.
   - **Agent Types**: $\text{Agent\_1} = \{a_1, a_3, a_7\}$, $\text{Agent\_2} = \{a_8\}$, $\text{Agent\_3} = \{a_2, a_4, a_5, a_6\}$.
   - **Odd-Path Violations in `Agent_3`**: Simple odd path $a_2 \rightharpoonup a_5$ (length 1, no repeated vertices) and odd walk $a_6 \rightharpoonup a_1 \rightharpoonup a_4 \rightharpoonup a_4$ (length 3, traversing self-loop $a_4 \rightharpoonup a_4$).
   - **Why Every Deviation Fails to Improve Utility**: When `Agent_1` and `Agent_2` report $\emptyset$, truthful revelation $S = \{a_2, a_4, a_5, a_6\}$ gives $E_{\text{truth}} = \{a_2, a_6\}$ ($u_3 = 2$). Hiding $a_2$ (e.g., revealing $S = \{a_5, a_6\}$ or $\{a_4, a_5, a_6\}$) genuinely rescues $a_5$ ($G = \{a_5\}, |G| = 1$), but doing so sacrifices $a_2$ ($L = \{a_2\}, |L| = 1$), leaving utility unchanged at $u_3 = 2$:

   | Revealed Subset $S \subseteq A_3$ | Induced $E_{grnd}(S)$ | Own Accepted $A_3 \cap E_{\text{dev}}$ | Rescued $G(S)$ | Sacrificed $L(S)$ | Utility $u_3(S)$ |
   | :--- | :--- | :--- | :--- | :--- | :---: |
   | $\emptyset$ or $\{a_4\}$ | $\emptyset$ | $\emptyset$ | $\emptyset$ | $\{a_2, a_6\}$ | $0$ |
   | $\{a_2\}, \{a_2, a_4\}, \{a_2, a_5\}, \{a_2, a_4, a_5\}$ | $\{a_2\}$ | $\{a_2\}$ | $\emptyset$ | $\{a_6\}$ | $1$ |
   | $\{a_5\}$ or $\{a_4, a_5\}$ | $\{a_5\}$ | $\{a_5\}$ | $\{a_5\}$ | $\{a_2, a_6\}$ | $1$ |
   | $\{a_6\}$ or $\{a_4, a_6\}$ | $\{a_6\}$ | $\{a_6\}$ | $\emptyset$ | $\{a_2\}$ | $1$ |
   | $\{a_5, a_6\}$ or $\{a_4, a_5, a_6\}$ | $\{a_5, a_6\}$ | $\{a_5, a_6\}$ | $\{a_5\}$ ($|G|=1$) | $\{a_2\}$ ($|L|=1$) | $2$ |
   | $\{a_2, a_6\}, \{a_2, a_4, a_6\}, \{a_2, a_5, a_6\}, \{a_2, a_4, a_5, a_6\}$ (Truthful) | $\{a_2, a_6\}$ | $\{a_2, a_6\}$ | $\emptyset$ | $\emptyset$ | **$2$** |

2. **`[p = 0.25, Instance #1006]` — Verified Category 1C: Odd Walk via Cycle, Target Unrescuable (`|G| = 0` in all profiles)**
   - **Framework**: $A = \{a_1, a_2, a_3, a_4, a_5, a_6\}$, $R = \{a_1 \rightharpoonup a_2, a_2 \rightharpoonup a_1, a_2 \rightharpoonup a_2, a_2 \rightharpoonup a_6, a_3 \rightharpoonup a_1, a_3 \rightharpoonup a_3, a_3 \rightharpoonup a_5, a_4 \rightharpoonup a_1, a_4 \rightharpoonup a_4, a_4 \rightharpoonup a_5\}$.
   - **Agent Types**: $\text{Agent\_1} = \{a_1, a_5, a_6\}$, $\text{Agent\_2} = \{a_3, a_4\}$, $\text{Agent\_3} = \{a_2\}$.
   - **Odd-Path Violation in `Agent_1`**: $a_1 \rightharpoonup a_2 \rightharpoonup a_2 \rightharpoonup a_6$ (length 3). Note that the simple path $a_1 \rightharpoonup a_2 \rightharpoonup a_6$ has even length 2, but traversing the self-loop $a_2 \rightharpoonup a_2$ creates an **odd-length directed walk** of length 3 with repeated vertex $a_2$.
   - **Why Strategyproof**: Across all opponent report profiles, `Agent_1` achieves $|G(S)| = 0$ for every subset $S \subseteq \{a_1, a_5, a_6\}$: whenever $a_2$ is revealed by `Agent_3`, $a_2 \rightharpoonup a_2$ makes $a_2$ undecided (`undec`), which blocks $a_6$ regardless of whether `Agent_1` reveals or hides $a_1$; and when $a_2$ is not revealed, $a_6$ is already unattacked and accepted under truthful revelation.

3. **`[p = 0.35, Instance #2008]` — Verified Category 1C: Simple Length-3 Odd Path, Target Independently Blocked (`|G| = 0` in all profiles)**
   - **Framework**: $A = \{a_1, a_2, a_3, a_4, a_5, a_6\}$, $R = \{a_1 \rightharpoonup a_2, a_2 \rightharpoonup a_1, a_2 \rightharpoonup a_2, a_2 \rightharpoonup a_6, a_3 \rightharpoonup a_2, a_3 \rightharpoonup a_6, a_5 \rightharpoonup a_2, a_6 \rightharpoonup a_1, a_6 \rightharpoonup a_3, a_6 \rightharpoonup a_6\}$.
   - **Agent Types**: $\text{Agent\_1} = \{a_6\}$, $\text{Agent\_2} = \{a_4, a_5\}$, $\text{Agent\_3} = \{a_1, a_2, a_3\}$.
   - **Odd-Path Violation in `Agent_3`**: Simple odd path $a_1 \rightharpoonup a_2 \rightharpoonup a_6 \rightharpoonup a_3$ (length 3, no repeated vertices) as well as $a_1 \rightharpoonup a_2$ and $a_3 \rightharpoonup a_2$ (length 1).
   - **Why Strategyproof**: Exhaustive verification across all opponent profiles confirms $\max |G(S)| = 0$. When `Agent_1` reveals $\{a_6\}$, $a_6 \rightharpoonup a_6$ makes $a_6$ undecided, so $a_6 \rightharpoonup a_1$ and $a_6 \rightharpoonup a_3$ block both $a_1$ and $a_3$ for all 8 subsets $S \subseteq \{a_1, a_2, a_3\}$ (`Own Accepted = empty, u = 0` for all 8 subsets); when `Agent_1` reports $\emptyset$, $a_3$ has no attackers and is accepted under truthful revelation.

---

### 4.4 Appendix: Sensitivity to Generator & Theorem 5.4 Design Choices

To ensure full transparency across alternative interpretations of the random instance generator (all $n^2$ directed attacks including self-attacks vs. $n(n-1)$ distinct-node attacks; non-empty 3-agent partitions vs. unrestricted i.i.d. agent assignments) and Theorem 5.4 pair scope (all $\alpha, \beta \in A_i$ vs. distinct $\alpha \neq \beta \in A_i$), the table below reports the exact counts across all $3,000$ instances (`seed=42`) computed by `demo.py`:

| Generator Configuration | Metric | $p = 0.15$ | $p = 0.25$ | $p = 0.35$ |
| :--- | :--- | :---: | :---: | :---: |
| **1. $n^2$ Attacks (Self-Attacks ON), Non-Empty Agents (Primary)** | Strategyproof (Thm 5.3) | $581 / 1000$ ($58.1\%$) | $235 / 1000$ ($23.5\%$) | $158 / 1000$ ($15.8\%$) |
| | Thm 5.4 Holds (All $\alpha, \beta \in A_i$) | $52$ ($5.2\%$) | $4$ ($0.4\%$) | $2$ ($0.2\%$) |
| | Thm 5.4 Holds (Distinct $\alpha \neq \beta$) | $137$ ($13.7\%$) | $11$ ($1.1\%$) | $5$ ($0.5\%$) |
| | **Thm 5.4 Holds & Fails SP (Q2)** | **$0$** | **$0$** | **$0$** |
| **2. $n^2$ Attacks (Self-Attacks ON), Unrestricted i.i.d. Agents** | Strategyproof (Thm 5.3) | $553 / 1000$ ($55.3\%$) | $256 / 1000$ ($25.6\%$) | $129 / 1000$ ($12.9\%$) |
| | Thm 5.4 Holds (All $\alpha, \beta \in A_i$) | $38$ ($3.8\%$) | $2$ ($0.2\%$) | $0$ ($0.0\%$) |
| | Thm 5.4 Holds (Distinct $\alpha \neq \beta$) | $81$ ($8.1\%$) | $10$ ($1.0\%$) | $1$ ($0.1\%$) |
| | **Thm 5.4 Holds & Fails SP (Q2)** | **$0$** | **$0$** | **$0$** |
| **3. $n(n-1)$ Attacks (No Self-Loops), Non-Empty Agents** | Strategyproof (Thm 5.3) | $640 / 1000$ ($64.0\%$) | $281 / 1000$ ($28.1\%$) | $111 / 1000$ ($11.1\%$) |
| | Thm 5.4 Holds (All $\alpha, \beta \in A_i$) | $167$ ($16.7\%$) | $27$ ($2.7\%$) | $4$ ($0.4\%$) |
| | Thm 5.4 Holds (Distinct $\alpha \neq \beta$) | $167$ ($16.7\%$) | $28$ ($2.8\%$) | $4$ ($0.4\%$) |
| | **Thm 5.4 Holds & Fails SP (Q2)** | **$0$** | **$0$** | **$0$** |
| **4. $n(n-1)$ Attacks (No Self-Loops), Unrestricted i.i.d. Agents** | Strategyproof (Thm 5.3) | $603 / 1000$ ($60.3\%$) | $309 / 1000$ ($30.9\%$) | $119 / 1000$ ($11.9\%$) |
| | Thm 5.4 Holds (All $\alpha, \beta \in A_i$) | $133$ ($13.3\%$) | $19$ ($1.9\%$) | $2$ ($0.2\%$) |
| | Thm 5.4 Holds (Distinct $\alpha \neq \beta$) | $135$ ($13.5\%$) | $20$ ($2.0\%$) | $2$ ($0.2\%$) |
| | **Thm 5.4 Holds & Fails SP (Q2)** | **$0$** | **$0$** | **$0$** |

Across all $4 \times 3,000 = 12,000$ random instances and both pair-scope conventions ($\alpha, \beta \in A_i$ vs. $\alpha \neq \beta \in A_i$), the number of instances satisfying Theorem 5.4 yet failing strategyproofness is identically **$0$**.
