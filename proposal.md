# Solution Proposal

## Algorithmic Methodology with Sandbox Parameter Optimization

The number search game is approached using a **two‑stage methodological framework**. A baseline heuristic is first introduced to expose the limitations of classical search under target drift. Building on this insight, a constraint‑based primary algorithm is then formulated to exploit the fact that the target increment $P$ is fixed throughout each game round. A sandbox pre‑run experiment is included to optimize the parameters used in both methodologies before deployment.

***

## 1. Baseline: Asymmetric Heuristic Search (AHS)

### Role of the Baseline

AHS is included as a **reference methodology**. Its purpose is to demonstrate how a simple modification of classical binary search can partially mitigate, but not fundamentally solve, the problem of a moving target.

***

### Algorithm Description

In standard binary search, the guess is placed at the midpoint of the current interval. In this problem, however, a guess that is too low (Case 3) causes the target value to increase, expanding the effective search range. Repeated midpoint guesses therefore risk a situation where the search interval grows faster than it shrinks.

AHS is rooted in the study of Adaptive Binary Search with Asymmetric Costs. It treats the target drift as an external disturbance, employing a conservative skew factor to manage the high cost of "Too Low" penalties.
***

### Guess Selection Rule

Let $[L, H]$ be the current search interval.  
The next guess $G$ is computed as:

$$
G = L + \lfloor \alpha (H - L) \rfloor
$$

where $\alpha \in (0.5, 1)$ is the skew factor.

***

### Update Rules

*   **Correct**: The algorithm terminates.
*   **Too High (−)**:
    $
    H \leftarrow G - 1
    $
*   **Too Low (+)**:
    $
    L \leftarrow G + 1, \quad H \leftarrow H + 200
    $

The upper bound expansion accounts for the maximum possible increment of the target.

***

### Limitation of the Baseline

Although AHS reduces the frequency of costly Case‑3 outcomes, it **treats target drift as an external disturbance**. It makes no attempt to infer the underlying increment $P$, and therefore cannot eliminate uncertainty about the system. As a result, the algorithm remains heuristic and susceptible to performance degradation in adverse cases.

***

## 2. Constraint-Based Version Space Search (CB-VSS)

### Conceptual Shift

The algorithm utilizes the Candidate Elimination framework. It treats the hidden parameters $(N_0, P)$ as a Version Space—the set of all hypotheses consistent with the observed server feedback. By applying deterministic linear constraints, the algorithm systematically prunes inconsistent hypotheses until the system is identified.  
***

### System Model

Let:

*   $N_0$ denote the unknown initial target value.
*   $P$ denote the unknown but fixed increment.
*   $c$ denote the number of “Too Low” responses encountered so far.

At any point, the current target value satisfies:

$$
N_t = N_0 + c \cdot P
$$

Thus, all uncertainty can be represented in the two‑dimensional parameter space $(N_0, P)$.

***

### Version Space Representation

The algorithm maintains a discrete Version Space over the joint parameter space $N_0 \in [1, 1000],P \in [1, 200]$. This is a form of Set-Membership Estimation used to bound uncertainty in non-stationary environments.

***

### Constraint Update Logic

Each server response introduces a linear inequality that eliminates inconsistent parameter pairs:

*   **Too High (−):**
    $
    N_0 + cP < G
    $
*   **Too Low (+):**
    $
    N_0 + cP > G
    $
    followed by incrementing $c$.

All pairs violating the inequality are removed from the feasible set, while the invariant that the true parameter pair remains feasible is preserved.

***

### Guess Selection Strategy

From the version space, the algorithm derives all possible current target values:

$
\{\, N_0 + cP \mid (N_0, P) \text{ is feasible} \,\}
$

This induces a discrete distribution over possible target locations. The next guess is selected as a **quantile** of this distribution. While the median minimizes expected guesses in a static search, slightly higher quantiles reduce the risk of triggering additional target increments before $P$ is uniquely identified.

***

### Convergence Mechanism

As constraints accumulate:

*   Infeasible values of $P$ are eliminated.
*   Once the feasible set collapses to a single value of $P$, the system is fully identified.
*   The remaining uncertainty lies only in $N_t$, reducing the problem to standard binary search without drift.

***

## 3. Sandbox Pre‑Run Experiment for Parameter Optimization

Before deployment, a sandbox environment is used to conduct controlled experiments to optimize algorithm parameters and validate convergence behavior.

***

### Environment Setup

The sandbox simulates the game with:

*   $N_0$ randomly sampled from $[1, 1000]$,
*   $P$ randomly sampled from $[1, 200]$,
*   $P$ held constant throughout each simulated game round.

This setup accurately reflects the assumptions of the server environment.

***

### Baseline Parameter Optimization

For AHS:

*   The skew factor $\alpha$ is swept over a predefined range (e.g., $[0.70, 0.95]$).
*   For each $\alpha$, multiple trials are run to measure average guess count and frequency of Case‑3 outcomes.
*   An empirically stable $\alpha$ value is selected that minimizes runaway interval expansion while maintaining reasonable convergence speed.

***

### Primary Algorithm Parameter Optimization

For the CB-VSS method:

*   Different quantile values $Q \in [0.50, 0.95]$ are tested for guess selection.
*   The primary metric measured is the number of Case‑3 events required to collapse the feasible $P$ range.
*   A quantile slightly above the median is typically preferred to balance information gain against early drift penalties.

***

### Outcome of the Pre‑Run

The sandbox experiments are used solely to:

*   Fix algorithm parameters before deployment,
*   Validate that the feasible set converges reliably,
*   Ensure that target drift does not lead to non‑termination.

No randomization is used in the deployed algorithm after parameters are selected.

***

## 4. Methodological Summary

The baseline AHS illustrates the limitations of reactive heuristics under target drift. The CB-VSS methodology systematically converts feedback into information about the hidden system parameters, guaranteeing monotonic reduction of uncertainty. Sandbox pre‑run experiments enable principled parameter selection, ensuring robust and efficient performance in the server environment.

| Component     | **Baseline: Asymmetric Heuristic Search (AHS)** | **Primary: Constraint-Based Version Space Search (CB-VSS)** |
|:--------------|:------------------------------------------------|:------------------------------------------------------------|
| **Logic**     | Reactive Heuristic                              | Deterministic Version Space Reduction                       |
| **Stability** | Vulnerable to "Death Spiral"                    | Immune to runaway expansion                                 |

---

### **4. New Section: Theoretical References**

**Add to the end of the document:**

> ### **References**
> *   **Problem Framework**: Ulam, S. M. (1976). *Adventures of a Mathematician*. (Foundational theory for **Ulam’s Searching Game with Drift**).
> *   **Baseline Theory**: Kapadia, S. (2020). *Adaptive Binary Search with Asymmetric Costs*.
> *   **Primary Methodology**: Mitchell, T. M. (1977). *"Version spaces: A candidate elimination approach to rule learning."* Artificial Intelligence.
> *   **System Identification**: Walter, É., & Piet-Lahanier, H. (1989). *"Exact recursive polyhedral description of the feasible parameter set for bounded-error models."* (Basis for **Set-Membership Estimation**).

