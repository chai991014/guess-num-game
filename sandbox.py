import random
from tqdm import tqdm
import time
import csv
from datetime import datetime


# ==========================================
# 1. SEARCH ALGORITHMS
# ==========================================

def asymmetric_heuristic_search(alpha):
    """
    Baseline: Asymmetric Heuristic Search (AHS)
    Rooted in Adaptive Binary Search with Asymmetric Costs.
    """
    n_initial = random.randint(1, 1000)
    p_fixed = random.randint(1, 200)  # P is rolled ONCE per game

    n_current = n_initial
    low, high = 1, 1000
    guesses = 0
    case3_count = 0

    while True:
        guesses += 1

        # Asymmetric guess based on alpha
        guess = low + int(alpha * (high - low))

        if guess == n_current:
            return guesses, case3_count, n_current

        elif guess > n_current:
            # Case 2: Too High (-) -> Target does not move
            high = guess - 1

        else:
            # Case 3: Too Low (+) -> Target moves by FIXED P
            low = guess + 1
            n_current += p_fixed
            high += 200
            case3_count += 1

        # Failsafe to prevent infinite loops (Death Spiral)
        if guesses > 3000:
            return guesses, case3_count, n_current


def constraint_based_version_space_search(quantile):
    """
    Main Solution: Constraint-Based Version Space Search (CB-VSS).
    Uses Candidate Elimination to prune a hypothesis space of (N0, P).
    """
    n_initial = random.randint(1, 1000)
    p_fixed = random.randint(1, 200)  # P is rolled ONCE per game

    n_current = n_initial
    guesses = 0
    case3_count = 0

    max_p = 200
    max_n_limit = 15000  # Safe upper bound

    # Initialize Feasible Set: dictionary mapping 'P' to a set of possible 'N's
    feasible_n_for_p = {p: set(range(1, 1001)) for p in range(1, max_p + 1)}

    while True:
        guesses += 1

        # 1. Pool all currently possible N values across all valid P's
        all_feasible_n = []
        for p in range(1, max_p + 1):
            all_feasible_n.extend(feasible_n_for_p[p])

        if not all_feasible_n:
            # Absolute failsafe if set collapses completely
            guess = 500
        else:
            all_feasible_n.sort()

            # 2. Select guess based on the Target Quantile
            target_idx = int(len(all_feasible_n) * quantile)
            if target_idx >= len(all_feasible_n):
                target_idx = len(all_feasible_n) - 1
            guess = all_feasible_n[target_idx]

        # 3. Evaluate Guess and Update Constraints
        if guess == n_current:
            return guesses, case3_count, n_current

        elif guess > n_current:
            # Case 2: Too High (-) -> Eliminate all N >= guess
            for p in range(1, max_p + 1):
                feasible_n_for_p[p] = {n for n in feasible_n_for_p[p] if n < guess}

        else:
            # Case 3: Too Low (+) -> Shift Target
            n_current += p_fixed
            case3_count += 1

            # Eliminate all N <= guess, then shift survivors right by P
            for p in range(1, max_p + 1):
                new_set = set()
                for n in feasible_n_for_p[p]:
                    if n > guess:
                        shifted_n = n + p
                        if shifted_n <= max_n_limit:
                            new_set.add(shifted_n)
                feasible_n_for_p[p] = new_set

        # Failsafe
        if guesses > 3000:
            return guesses, case3_count, n_current


# ==========================================
# 2. EXPERIMENT ENGINE
# ==========================================

def run_experiment(algorithm_name, func, trials=1000, use_tqdm=False, **kwargs):
    """Runs bulk trials and calculates evaluation metrics."""
    total_guesses = 0
    total_case3 = 0
    max_n_reached = 0
    death_spiral_count = 0

    desc = f"{algorithm_name}"
    if kwargs:
        desc += f" {kwargs}"

    loop_iterator = tqdm(range(trials), desc=desc, ncols=100, leave=False) if use_tqdm else range(trials)

    start_time = time.time()

    for _ in loop_iterator:
        guesses, case3, final_n = func(**kwargs)

        total_guesses += guesses
        total_case3 += case3
        if final_n > max_n_reached:
            max_n_reached = final_n

        if guesses > 3000:
            death_spiral_count += 1

    end_time = time.time()
    elapsed_time = end_time - start_time

    mean_guesses = total_guesses / trials
    case3_freq = (total_case3 / total_guesses) * 100
    death_spiral_rate = (death_spiral_count / trials) * 100

    print(f"--- {algorithm_name} ---")
    if kwargs:
        print(f"Parameters : {kwargs}")
    print(f"Mean Guesses   : {mean_guesses:.2f}")
    print(f"Case 3 Freq    : {case3_freq:.2f}%")
    print(f"Max Drift (N)  : {max_n_reached}")
    print(f"Death Spirals  : {death_spiral_rate:.2f}%")
    print(f"Time Taken     : {elapsed_time:.4f}s")
    print("-" * 30)

    return {
        "Algorithm": algorithm_name,
        "Parameters": str(kwargs),
        "Mean Guesses": round(mean_guesses, 2),
        "Case 3 Freq (%)": round(case3_freq, 2),
        "Max Drift (N)": max_n_reached,
        "Death Spiral Rate (%)": round(death_spiral_rate, 2),
        "Time (s)": round(elapsed_time, 4)
    }


if __name__ == "__main__":
    TRIALS = 2000
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_headers = ["Algorithm", "Parameters", "Mean Guesses", "Case 3 Freq (%)", "Max Drift (N)", "Death Spiral Rate (%)", "Time (s)"]

    # --- 1. Asymmetric Heuristic Search Parameter Sweep ---
    ahs_results = []
    print("\nStarting Parameter Sweep for Asymmetric Heuristic Search...")
    test_alphas = [a / 100 for a in range(50, 100)]

    for a in test_alphas:
        res = run_experiment("Asymmetric Heuristic Search (AHS)", asymmetric_heuristic_search, trials=TRIALS, alpha=a)
        ahs_results.append(res)

    with open(f'./results/ahs_sweep_{timestamp}.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(ahs_results)
    print(f">>> Saved ahs_sweep_{timestamp}.csv\n")

    # --- 2. Constraint-Based Version Space Search Parameter Sweep ---
    vss_results = []
    print("\nStarting Parameter Sweep for Constraint-Based Version Space Search...")
    test_quantiles = [q / 100 for q in range(40, 96, 5)]

    for q in test_quantiles:
        res = run_experiment("Constraint-Based Version Space Search (CB-VSS)", constraint_based_version_space_search, trials=TRIALS, use_tqdm=True, quantile=q)
        vss_results.append(res)

    with open(f'./results/vss_sweep_{timestamp}.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(vss_results)
    print(f">>> Saved vss_sweep_{timestamp}.csv")

    print("\nSandbox execution complete. Review the CSV files to select optimal parameters.")
