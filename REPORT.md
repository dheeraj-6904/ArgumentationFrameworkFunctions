# Assignment 3 Technical Report: Argumentation Engine & Strategic Argumentation

---

## 1. Executive Summary

This report presents the design, theoretical verification, and experimental evaluation of:
1. **Part 1 — Abstract Argumentation Engine**: A full implementation of Dung's abstract argumentation framework $\langle A, \rightharpoonup \rangle$, conflict-freeness, argument defense, the characteristic function $F_{AF}(S)$, admissibility, extension-based semantics (**grounded**, **complete**, **preferred**, **stable**, and **semi-stable**), Caminada's **legal (`in`/`out`/`undec`) labellings**, and argument acceptance status (**skeptically accepted**, **credulously accepted**, **rejected**).
2. **Part 2 — Strategic Argumentation (Grounded Direct Argumentation Mechanism)**: An implementation of the multi-agent mechanism $\mathcal{M}_{AF}^{grnd}$, optimal subset revelation (best-response search), exact strategyproofness verification (**Theorem 5.3**), and cycle-aware odd-length directed path verification (**Theorem 5.4**).
3. **Part 3 — Monte Carlo Experiments**: A statistical investigation across **3,000 random instances** (1,000 instances for each attack probability $p \in \{0.15, 0.25, 0.35\}$, with $n \in \{6, 7, 8\}$ arguments randomly partitioned among 3 agents).

---

## 2. Part 1: Argumentation Engine & Book Example Verification

### 2.1 Architecture & Algorithmic Summary
- **Dual-Adjacency Graph Representation (`src/framework.py`)**: `ArgumentationFramework` pre-indexes incoming attackers ($\{\beta \in A \mid \beta \rightharpoonup \alpha\}$) and outgoing targets ($\{\beta \in A \mid \alpha \rightharpoonup \beta\}$) for each argument. Consequently, computing the defeated range $S^+ = \{\beta \in A \mid \exists \gamma \in S, \gamma \rightharpoonup \beta\}$ and testing defense ($\text{attackers}(\alpha) \subseteq S^+$) execute in $O(|S|)$ set operations.
- **Grounded Extension (`src/semantics.py`)**: Computed in polynomial time $O(|A|^3)$ as the least fixed point of the monotonic characteristic function $F_{AF}(S) = \{\alpha \in A \mid \text{attackers}(\alpha) \subseteq S^+\}$, iterating $S_{k+1} = F_{AF}(S_k)$ from $S_0 = \emptyset$ until convergence.
- **Complete, Preferred, Stable, and Semi-Stable Extensions (`src/semantics.py`)**:
  - Every complete extension $E$ satisfies $E_{grnd} \subseteq E \subseteq A \setminus (E_{grnd} \cup E_{grnd}^+)$. We seed a pruned backtracking search with $E_{grnd}$, immediately pruning any branch that introduces an internal conflict or self-attack, and collect fixed points satisfying $F_{AF}(E) = E$.
  - **Preferred extensions** are extracted as the $\subseteq$-maximal complete extensions.
  - **Stable extensions** are extracted as complete extensions satisfying $E \cup E^+ = A$.
  - **Semi-stable extensions** are extracted as complete extensions whose range $E \cup E^+$ is $\subseteq$-maximal among all complete extensions.
- **Legal Labellings (`src/labelling.py`)**: Each complete extension $E$ maps bijectively to a legal labelling $\mathcal{L}_E$ with $\text{in}(\mathcal{L}_E) = E$, $\text{out}(\mathcal{L}_E) = E^+$, and $\text{undec}(\mathcal{L}_E) = A \setminus (E \cup E^+)$, verified directly against Caminada's three local legality conditions.

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

### 3.3 Dealing with Cycles in Theorem 5.4
A naive graph search that maintains a single `visited` set of vertices fails on cyclic or reconvergent graphs: if a vertex $v$ is first visited from $\alpha$ along an **even-length** path, $v$ is marked visited and never re-explored along an **odd-length** path or cycle. To handle arbitrary cycles rigorously, `src/strategic.py` implements:
1. `find_odd_length_simple_path`: Backtracking DFS with branch-local cycle avoidance (`on_path`), allowing any vertex to be visited under both parities across distinct branches.
2. `find_odd_length_walk`: Parity-State BFS on the product state space $A \times \{0, 1\}$, tracking reachability of `(vertex, parity)` in $O(|A| + |\rightharpoonup|)$ time without infinite loops on cycles.

---

## 4. Part 3: Experimental Results & Analysis

### 4.1 Experimental Setup
- **Agents**: 3 agents (`Agent_1`, `Agent_2`, `Agent_3`).
- **Arguments**: $n \in \{6, 7, 8\}$ chosen uniformly at random per instance, partitioned uniformly at random among the 3 agents.
- **Attack Probabilities**: $p \in \{0.15, 0.25, 0.35\}$, where each directed attack $(\alpha_u, \alpha_v)$ ($u \neq v$) is present independently with probability $p$.
- **Sample Size**: **1,000 random instances per $p$** (**3,000 instances total**, seed `42`).

### 4.2 Summary Table (Question 1, Question 2, Question 3)

| Attack Prob $p$ | Total Instances | Strategyproof (Theorem 5.3 Holds) | Fraction Strategyproof | Theorem 5.4 Condition Holds | Thm 5.4 Holds & Fails SP (Q2) | Strategyproof Despite Thm 5.4 Failing (Q3) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$0.15$** | $1000$ | $603$ | **$0.6030$ ($60.3\%$)** | $133$ ($13.3\%$) | **$0$ ($0.0\%$)** | $470$ ($47.0\%$) |
| **$0.25$** | $1000$ | $309$ | **$0.3090$ ($30.9\%$)** | $19$ ($1.9\%$) | **$0$ ($0.0\%$)** | $290$ ($29.0\%$) |
| **$0.35$** | $1000$ | $119$ | **$0.1190$ ($11.9\%$)** | $2$ ($0.2\%$) | **$0$ ($0.0\%$)** | $117$ ($11.7\%$) |
| **Total** | **$3000$** | **$1031$** | **$0.3437$ ($34.4\%$)** | **$154$ ($5.1\%$)** | **$0$ ($0.0\%$)** | **$877$ ($29.2\%$)** |

---

### 4.3 Detailed Answers to Experimental Questions

#### Question 1: Fraction of Instances that are Strategyproof for Each $p$
- For **$p = 0.15$**: **$0.6030$ ($60.3\%$)** of instances are strategyproof.
- For **$p = 0.25$**: **$0.3090$ ($30.9\%$)** of instances are strategyproof.
- For **$p = 0.35$**: **$0.1190$ ($11.9\%$)** of instances are strategyproof.
- **Trend**: As attack density $p$ increases from $0.15$ to $0.35$, the graph becomes significantly more connected and cyclic, creating many more odd-length paths (both direct conflicts and multi-step indirect self-defeats) within each agent's argument set. Consequently, the probability that an agent can strategically withhold an argument to break an odd-length self-defeat chain or resolve a cycle in its favor rises sharply, reducing the strategyproof fraction from $60.3\%$ down to $11.9\%$.

---

#### Question 2: How Many Instances Satisfy the Condition in Theorem 5.4 Yet Fail Strategyproofness?
- **Result**: **$0$ instances** (out of $3,000$ total instances across all $p \in \{0.15, 0.25, 0.35\}$) satisfy Theorem 5.4's condition yet fail strategyproofness.
- **Mathematical Explanation**:
  Theorem 5.4 is a mathematically proven **sufficient condition** ($\text{Theorem 5.4 Condition} \implies \text{Strategyproofness}$). Specifically, suppose agent $i$ reveals an additional argument $\alpha \in A_i$ on top of a subset $S \subseteq A_i$. By induction on the iterations $F_{AF}^k(\emptyset)$ of the characteristic function:
  1. Any argument $x$ that was accepted without $\alpha$ but fails to be accepted when $\alpha$ is revealed must be reachable from $\alpha$ by an **odd-length directed path/walk** ($\alpha \rightharpoonup^{2m+1} x$).
  2. Any argument $y$ that was defeated without $\alpha$ but ceases to be defeated when $\alpha$ is revealed must be reachable from $\alpha$ by an **even-length directed path/walk** ($\alpha \rightharpoonup^{2m} y$).
  Therefore, if no two arguments $\alpha, \beta \in A_i$ have an odd-length directed path from $\alpha$ to $\beta$, revealing $\alpha$ can **never** cause any $\beta \in A_i$ to be excluded from the grounded extension! Revealing more arguments can only monotonically preserve or expand $A_i \cap E_{grnd}$, making truthful revelation a dominant strategy.
- **Why Cycle & Direct-Attack Handling is Critical**:
  If an implementation of Theorem 5.4 only checks indirect paths of length $\ge 3$ while ignoring length-1 direct attacks ($\alpha \rightharpoonup \beta$), it produces **182 false positives** ($106$ at $p=0.15$, $61$ at $p=0.25$, $15$ at $p=0.35$). For example, in **Instance #9 ($p = 0.15$)**:
  - $A = \{a_1, \dots, a_8\}$, $R = \{a_2 \rightharpoonup a_1, a_2 \rightharpoonup a_6, a_3 \rightharpoonup a_7, a_4 \rightharpoonup a_2, a_4 \rightharpoonup a_8, a_8 \rightharpoonup a_4\}$.
  - `Agent_1` holds $\{a_2, a_3, a_4, a_5, a_8\}$. Here $a_4 \leftrightarrow a_8$ forms a 2-cycle (making both $a_4$ and $a_8$ undecided), while $a_4 \rightharpoonup a_2$ (length 1, odd) blocks $a_2$! When `Agent_1` reveals truthfully, only $\{a_3, a_5\}$ are accepted ($u_1 = 2$); by hiding $a_4$ (and $a_8$) and revealing $\{a_2, a_3, a_5\}$, $\{a_2, a_3, a_5\}$ are all accepted ($u_1 = 3 > 2$). Because our Theorem 5.4 checker properly tests all odd path lengths $1, 3, 5, \dots$ and handles cycles via parity reachability, it achieves **zero** false positives.

---

#### Question 3: Are There Instances that are Strategyproof Although Theorem 5.4's Condition Fails?
- **Result**: **Yes — $877$ out of $3,000$ instances ($29.2\%$)** are strategyproof even though Theorem 5.4's condition fails:
  - **$p = 0.15$**: **$470 / 1000$ ($47.0\%$)** instances (out of $603$ strategyproof instances, $77.9\%$ violate Theorem 5.4!).
  - **$p = 0.25$**: **$290 / 1000$ ($29.0\%$)** instances (out of $309$ strategyproof instances, $93.9\%$ violate Theorem 5.4!).
  - **$p = 0.35$**: **$117 / 1000$ ($11.7\%$)** instances (out of $119$ strategyproof instances, $98.3\%$ violate Theorem 5.4!).
- **Why Are They Strategyproof? (Structural Classification & Concrete Instances)**:
  Theorem 5.4 is **sufficient but not necessary**. Across the $877$ instances where Theorem 5.4 fails yet the mechanism remains strategyproof, our structural analyzer classifies the reasons into three mechanisms:

  1. **Direct Internal Conflict Swap Neutrality ($462$ instances: $314$ at $p=0.15$, $123$ at $p=0.25$, $25$ at $p=0.35$)**:
     - The agent has a length-1 direct attack $\alpha \rightharpoonup \beta$ between two of its own arguments ($\alpha, \beta \in A_i$), where $\alpha$ itself is accepted when revealed and attacks at most one otherwise-accepted argument $\beta \in A_i$.
     - If the agent hides $\alpha$ to rescue $\beta$, the agent **loses $\alpha$ ($-1$ utility)** and **gains at most $\beta$ ($+1$ utility)**, resulting in a net utility change of $\le 0$. Thus, hiding $\alpha$ never strictly improves utility.

  2. **Indirect Odd Path Cancellation or 1-for-1 Bounding — Example 5.11 Type ($412$ instances: $154$ at $p=0.15$, $166$ at $p=0.25$, $92$ at $p=0.35$)**:
     - An agent holds $\alpha, \beta \in A_i$ connected by an indirect odd-length path $\alpha \rightharpoonup \gamma_1 \rightharpoonup \gamma_2 \rightharpoonup \dots \rightharpoonup \beta$ (length $\ge 3$), but either:
       - **(a) Path Cancellation (as in Book Example 5.11)**: Another argument (held by the agent or revealed simultaneously) defeats an intermediate node $\gamma_k$ along the path or independently defeats $\beta$, rendering the indirect self-defeat inactive under grounded semantics; or
       - **(b) 1-for-1 Tradeoff**: Revealing $\alpha$ gets $\alpha$ accepted while indirectly defeating only a single argument $\beta \in A_i$, so hiding $\alpha$ trades $\alpha$ for $\beta$ ($+1 - 1 = 0$ net gain).
     - **Concrete Noted Instance (`p = 0.15, Instance #1`)**:
       - $A = \{a_1, \dots, a_8\}$, $R = \{a_1 \rightharpoonup a_2, a_1 \rightharpoonup a_5, a_1 \rightharpoonup a_6, a_2 \rightharpoonup a_3, a_2 \rightharpoonup a_4, a_4 \rightharpoonup a_6, a_5 \rightharpoonup a_3, a_5 \rightharpoonup a_6, a_5 \rightharpoonup a_8, a_6 \rightharpoonup a_7, a_8 \rightharpoonup a_6\}$.
       - Agent types: $\text{Agent\_1} = \{a_3, a_4\}$, $\text{Agent\_2} = \{a_5, a_6, a_7\}$, $\text{Agent\_3} = \{a_1, a_2, a_8\}$.
       - `Agent_2` has the odd-length path $a_5 \rightharpoonup a_8 \rightharpoonup a_6 \rightharpoonup a_7$ (length 3) as well as $a_5 \rightharpoonup a_6$ (length 1). However, $a_5$ also directly attacks $a_6$ ($a_5 \rightharpoonup a_6$), which **defends** $a_7$! Thus, revealing $a_5$ gets both $a_5$ and $a_7$ accepted (or when $a_1$ is revealed by `Agent_3`, $a_1$ defeats both $a_5$ and $a_6$ directly, keeping $a_7$ defended). Across every combination of opponent reports, truthful revelation is optimal for all 3 agents.
     - **Concrete Noted Instance (`p = 0.25, Instance #1002`)**:
       - $A = \{a_1, \dots, a_7\}$, $R = \{a_1 \rightharpoonup a_6, a_3 \rightharpoonup a_4, a_3 \rightharpoonup a_5, a_3 \rightharpoonup a_6, a_4 \rightharpoonup a_1, a_4 \rightharpoonup a_6, a_6 \rightharpoonup a_7, a_7 \rightharpoonup a_1, a_7 \rightharpoonup a_4, a_7 \rightharpoonup a_6\}$.
       - Agent types: $\text{Agent\_1} = \{a_1, a_2, a_3, a_7\}$, $\text{Agent\_2} = \{a_4, a_5, a_6\}$, $\text{Agent\_3} = \emptyset$.
       - `Agent_1` has the length-3 odd path $a_3 \rightharpoonup a_4 \rightharpoonup a_6 \rightharpoonup a_7$. However, `Agent_1`'s unattacked argument $a_3$ also directly attacks $a_6$ ($a_3 \rightharpoonup a_6$), immediately cancelling $a_6$'s attack on $a_7$ (exactly mirroring Example 5.11!).

  3. **Odd Self-Cycle Only ($3$ instances: $2$ at $p=0.15$, $1$ at $p=0.25$, $0$ at $p=0.35$)**:
     - The only odd-length walks within $A_i$ start and end at the same argument ($\alpha \rightharpoonup \dots \rightharpoonup \alpha$). Because hiding $\alpha$ removes $\alpha$ from the induced subgraph anyway, withholding $\alpha$ can never cause $\alpha$ or any other argument in $A_i$ to become accepted.
