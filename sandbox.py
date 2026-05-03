import random
from tqdm import tqdm
import time
import csv


# ==========================================
# 1. SEARCH ALGORITHMS
# ==========================================

def binary_baseline_search():
    """Standard Binary Search (50% split) for baseline comparison."""
    n = random.randint(1, 1000)
    low, high = 1, 1000
    guesses = 0
    case3_count = 0

    while True:
        guesses += 1
        guess = low + (high - low) // 2

        if guess == n:
            return guesses, case3_count, n
        elif guess > n:
            high = guess - 1
        else:
            low = guess + 1
            n += random.randint(1, 200)
            high += 200
            case3_count += 1


def risk_optimized_skew_search(alpha):
    """Unified Search using a Skew Factor (alpha) to avoid Case 3."""
    n = random.randint(1, 1000)
    low, high = 1, 1000
    guesses = 0
    case3_count = 0

    while True:
        guesses += 1
        # Skew the guess towards the upper bound
        guess = low + int(alpha * (high - low))

        if guess == n:
            return guesses, case3_count, n
        elif guess > n:
            high = guess - 1
        else:
            low = guess + 1
            n += random.randint(1, 200)
            high += 200
            case3_count += 1


def bayesian_probabilistic_search(quantile):
    """Belief-based search using a probability distribution and stochastic shifts."""
    n = random.randint(1, 1000)
    max_horizon = 6000  # Max possible N to prevent array index out of bounds
    probs = [0.0] * max_horizon

    # Initialize uniform prior for 1 to 1000
    for i in range(1, 1001):
        probs[i] = 1.0 / 1000.0

    guesses = 0
    case3_count = 0

    while guesses < 200:
        guesses += 1

        # Determine guess based on cumulative probability and target quantile
        cum_prob = 0.0
        guess = max_horizon // 2
        for i in range(1, max_horizon):
            cum_prob += probs[i]
            if cum_prob >= quantile:
                guess = i
                break

        if guess == n:
            return guesses, case3_count, n

        elif guess > n:
            # Case 2: Zero out impossible high values
            for i in range(guess, max_horizon):
                probs[i] = 0.0

            # Renormalize distribution
            total_prob = sum(probs)
            if total_prob > 0:
                probs = [p / total_prob for p in probs]
            else:
                # Fallback if distribution collapses
                probs = [1.0 / guess if i < guess else 0.0 for i in range(max_horizon)]

        else:
            # Case 3: N increases by P
            case3_count += 1
            n += random.randint(1, 200)

            # Zero out impossible low values
            for i in range(0, guess + 1):
                probs[i] = 0.0

            # Perform stochastic shift (discrete convolution with uniform P)
            # Using a sliding window sum for O(N) performance without external libraries
            new_probs = [0.0] * max_horizon
            window_sum = 0.0
            for i in range(max_horizon):
                if i >= 1:
                    window_sum += probs[i - 1]
                if i >= 201:
                    window_sum -= probs[i - 201]

                window_sum = max(0.0, window_sum)
                new_probs[i] = window_sum / 200.0

            probs = new_probs

            # Renormalize distribution
            total_prob = sum(probs)
            if total_prob > 0:
                probs = [p / total_prob for p in probs]
            else:
                # Fallback if distribution collapses
                probs = [1.0 / max_horizon] * max_horizon

    return guesses, case3_count, n


# ==========================================
# 2. EXPERIMENT ENGINE
# ==========================================

def run_experiment(algorithm_name, func, trials=1000, use_tqdm=False, **kwargs):
    """Runs bulk trials and calculates evaluation metrics."""
    total_guesses = 0
    total_case3 = 0
    max_n_reached = 0

    # Format the progress bar label
    desc = f"{algorithm_name}"
    if kwargs:
        desc += f" {kwargs}"

    # Conditionally wrap the range() with tqdm
    loop_iterator = tqdm(range(trials), desc=desc, ncols=100, leave=False) if use_tqdm else range(trials)

    start_time = time.time()

    for _ in loop_iterator:
        if kwargs:
            guesses, case3, final_n = func(**kwargs)
        else:
            guesses, case3, final_n = func()

        total_guesses += guesses
        total_case3 += case3
        if final_n > max_n_reached:
            max_n_reached = final_n

    end_time = time.time()
    elapsed_time = end_time - start_time

    mean_guesses = total_guesses / trials
    case3_freq = (total_case3 / total_guesses) * 100

    print(f"--- {algorithm_name} ---")
    if kwargs:
        print(f"Parameters : {kwargs}")
    print(f"Mean Guesses   : {mean_guesses:.2f}")
    print(f"Case 3 Freq    : {case3_freq:.2f}%")
    print(f"Max Drift (N)  : {max_n_reached}")
    print(f"Time Taken     : {elapsed_time:.4f}s")
    print("-" * 30)

    return {
        "Algorithm": algorithm_name,
        "Parameters": str(kwargs) if kwargs else "None",
        "Mean Guesses": round(mean_guesses, 2),
        "Case 3 Freq (%)": round(case3_freq, 2),
        "Max Drift (N)": max_n_reached,
        "Time (s)": round(elapsed_time, 4)
    }


if __name__ == "__main__":
    print("Initializing WQF7004 Number Search Sandbox...\n")
    TRIALS = 2000

    # 1. Run Baseline
    run_experiment("Binary Baseline", binary_baseline_search, trials=TRIALS)

    skew_results = []
    bayesian_results = []
    csv_headers = ["Algorithm", "Parameters", "Mean Guesses", "Case 3 Freq (%)", "Max Drift (N)", "Time (s)"]

    # 2. Parameter Sweep for Risk-Optimized Skew
    print("\nStarting Parameter Sweep for Skew Search...")
    test_alphas = [a / 100 for a in range(60, 91)]
    for a in test_alphas:
        res = run_experiment("Risk-Optimized Skew", risk_optimized_skew_search, trials=TRIALS, alpha=a)
        skew_results.append(res)

    with open('skew_results.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(skew_results)
    print("\n>>> Saved skew_results.csv")

    # 3. Parameter Sweep for Bayesian Probabilistic Search
    print("\nStarting Parameter Sweep for Bayesian Search...")
    test_quantiles = [q / 100 for q in range(75, 91)]
    for q in test_quantiles:
        res = run_experiment("Bayesian Search", bayesian_probabilistic_search, trials=TRIALS, use_tqdm=True, quantile=q)
        bayesian_results.append(res)

    with open('bayesian_results.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(bayesian_results)
    print("\n>>> Saved bayesian_results.csv")
