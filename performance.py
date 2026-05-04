import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast
import re
import os
import glob

results_path = './results/'
# ahs_files = sorted(glob.glob(os.path.join(results_path, "initial_ahs_sweep.csv")))
# vss_files = sorted(glob.glob(os.path.join(results_path, "initial_vss_sweep.csv")))

ahs_files = sorted(glob.glob(os.path.join(results_path, "ahs_sweep_*.csv")))
vss_files = sorted(glob.glob(os.path.join(results_path, "vss_sweep_*.csv")))

def load_and_process(file_list, algorithm_label):
    """Loads CSVs from the found list, adds a run ID, and extracts parameters."""
    all_dfs = []
    if not file_list:
        print(f"Warning: No files found for {algorithm_label} in {results_path}")
        return pd.DataFrame()

    for i, file in enumerate(file_list):
        df = pd.read_csv(file)
        df['Run_ID'] = i + 1
        df['Algorithm_Type'] = algorithm_label

        # Extract numeric parameter (alpha or quantile) from the Parameters string
        def get_val(p_str):
            try:
                p_dict = ast.literal_eval(p_str)
                return float(list(p_dict.values())[0])
            except:
                # Regex fallback if ast fails
                match = re.search(r'(\d+\.\d+)', str(p_str))
                return float(match.group(1)) if match else None

        df['Param_Value'] = df['Parameters'].apply(get_val)
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)


# Combine and aggregate data
df_ahs = load_and_process(ahs_files, "Asymmetric Heuristic Search (AHS)")
df_vss = load_and_process(vss_files, "Constraint-Based Version Space Search (CB-VSS)")
combined_df = pd.concat([df_ahs, df_vss], ignore_index=True)

if combined_df.empty:
    print("No data found. Please run the sandbox 5 times to generate CSV files.")
    exit()

# Calculate aggregated means across all 5 runs
agg_stats = combined_df.groupby(['Algorithm_Type', 'Param_Value']).mean(numeric_only=True).reset_index()

# Find optimal configurations (lowest Mean Guesses)
best_ahs = agg_stats[agg_stats['Algorithm_Type'] == "Asymmetric Heuristic Search (AHS)"].sort_values('Mean Guesses').iloc[0]
best_vss = agg_stats[agg_stats['Algorithm_Type'] == "Constraint-Based Version Space Search (CB-VSS)"].sort_values('Mean Guesses').iloc[0]

# Combine the "Best" performers into one dataframe for plotting
best_models_data = [
    {
        'Algorithm': f'AHS\n(Alpha {best_ahs["Param_Value"]:.2f})',
        'Mean Guesses': best_ahs['Mean Guesses'],
        'Max Drift': best_ahs['Max Drift (N)'],
        'Case 3 Freq (%)': best_ahs['Case 3 Freq (%)'],
        'Death Spiral Rate (%)': best_ahs['Death Spiral Rate (%)']
    },
    {
        'Algorithm': f'CB-VSS\n(Quantile {best_vss["Param_Value"]:.2f})',
        'Mean Guesses': best_vss['Mean Guesses'],
        'Max Drift': best_vss['Max Drift (N)'],
        'Case 3 Freq (%)': best_vss['Case 3 Freq (%)'],
        'Death Spiral Rate (%)': best_vss['Death Spiral Rate (%)']
    }
]

df_best = pd.DataFrame(best_models_data)

# ==========================================
# 2. GENERATE PLOTS
# ==========================================

# Create the main figure
fig1 = plt.figure(figsize=(14, 11)) # Slightly taller to accommodate the suptitle
sns.set_theme(style="whitegrid")

# --- Global Title for Line Plots ---
# fig1.suptitle('Algorithm Performance & Stability Analysis\n(No. of Trials = 2000)', fontweight='bold', fontsize=16, y=0.96)

fig1.suptitle('Algorithm Performance & Stability Analysis\n(Aggregated over 5 Runs | No. of Trials = 2000 per Run)',
              fontweight='bold', fontsize=16, y=0.97)

# --- Plot 1: Performance Trend Subplot ---
plt.subplot(3, 1, 1)
sns.lineplot(data=combined_df, x='Param_Value', y='Mean Guesses', hue='Algorithm_Type', marker='o', errorbar='sd')

# Annotation for AHS
plt.scatter(best_ahs['Param_Value'], best_ahs['Mean Guesses'], color='blue', s=120, zorder=5)
plt.annotate(f"Min: {best_ahs['Mean Guesses']:.2f}\nAlpha (AHS): {best_ahs['Param_Value']}",
             xy=(best_ahs['Param_Value'], best_ahs['Mean Guesses']),
             xytext=(best_ahs['Param_Value']-0.05, best_ahs['Mean Guesses']-300),
             arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

# Annotation for CB-VSS
plt.scatter(best_vss['Param_Value'], best_vss['Mean Guesses'], color='orange', s=120, zorder=5)
plt.annotate(f"Min: {best_vss['Mean Guesses']:.2f}\nQuantile (CB-VSS): {best_vss['Param_Value']}",
             xy=(best_vss['Param_Value'], best_vss['Mean Guesses']),
             xytext=(best_vss['Param_Value']-0.05, best_vss['Mean Guesses']*2.0),
             arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

plt.title('Mean Guesses Optimization (Log Scale)', fontsize=13)
plt.ylabel('Mean Guesses')
plt.yscale('log') # Essential for viewing Skew and LCS together
plt.legend()

# --- Plot 2: Drift Stability Subplot ---
plt.subplot(3, 1, 2)
sns.lineplot(data=combined_df, x='Param_Value', y='Max Drift (N)', hue='Algorithm_Type', marker='s', errorbar='sd')
plt.title('Maximum Drift Stability Analysis (Log Scale)', fontsize=13)
plt.ylabel('Max Drift (N)')
plt.yscale('log') # Essential due to ~600,000 vs ~3,000 drift differences

# --- Plot 3: Death Spiral Rate Subplot ---
plt.subplot(3, 1, 3)
sns.lineplot(data=combined_df, x='Param_Value', y='Death Spiral Rate (%)', hue='Algorithm_Type', marker='^', errorbar='sd')
plt.title('Catastrophic Failure Rate (Death Spirals > 3000 Guesses)', fontsize=13)
plt.ylabel('Death Spiral Rate (%)')
plt.legend()

plt.tight_layout(rect=[0, 0, 1, 0.95])
os.makedirs('results', exist_ok=True)
plt.savefig('results/aggregated_analysis.png', dpi=300)
print(f"Line plots complete. Found {len(ahs_files)} AHS and {len(vss_files)} VSS files.")
print("Visualization saved as 'results/aggregated_analysis.png'.")
plt.show()

# --- Plot 3: Bar Chart Comparison of Best Models ---
if not df_best.empty:
    fig2, axes = plt.subplots(1, 4, figsize=(20, 6))
    # fig2.suptitle('Optimal Algorithm Comparison\n(No. of Trials = 2000)', fontweight='bold', fontsize=16, y=1.02)

    fig2.suptitle('Optimal Algorithm Comparison\n(Aggregated over 5 Runs | No. of Trials = 2000 per Run)',
                  fontweight='bold', fontsize=16, y=1.02)

    # Subplot A: Mean Guesses
    sns.barplot(data=df_best, x='Algorithm', y='Mean Guesses', hue='Algorithm', legend=False, ax=axes[0], palette=['#3498db', '#e67e22'])
    axes[0].set_title('Efficiency (Mean Guesses)')
    for container in axes[0].containers:
        axes[0].bar_label(container, fmt='%.2f', label_type='edge', padding=3)

    # Subplot B: Max Drift
    sns.barplot(data=df_best, x='Algorithm', y='Max Drift', hue='Algorithm', legend=False, ax=axes[1], palette=['#3498db', '#e67e22'])
    axes[1].set_title('Stability (Max Drift N)')
    for container in axes[1].containers:
        axes[1].bar_label(container, fmt='%.0f', label_type='edge', padding=3)

    # Subplot C: Case 3 Frequency
    sns.barplot(data=df_best, x='Algorithm', y='Case 3 Freq (%)', hue='Algorithm', legend=False, ax=axes[2], palette=['#3498db', '#e67e22'])
    axes[2].set_title('Target Increment Frequency (%)')
    for container in axes[2].containers:
        axes[2].bar_label(container, fmt='%.1f%%', label_type='edge', padding=3)

    # Subplot D: Death Spiral Rate
    sns.barplot(data=df_best, x='Algorithm', y='Death Spiral Rate (%)', hue='Algorithm', legend=False, ax=axes[3],
                palette=['#e74c3c', '#2ecc71'])
    axes[3].set_title('Failure Rate (%)')
    for container in axes[3].containers:
        axes[3].bar_label(container, fmt='%.1f%%', label_type='edge', padding=3)

    plt.tight_layout()
    plt.savefig('results/best_algorithms_comparison.png', dpi=300, bbox_inches='tight')
    print("Bar chart comparison saved as 'results/best_algorithms_comparison.png'")
    plt.show()
