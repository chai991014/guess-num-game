import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast
import os
import glob

# 1. Dynamically load all CSV files from the ./results/ folder
results_path = './results/'

# Finds all files matching the pattern and sorts them to maintain consistent Run_IDs
skew_files = sorted(glob.glob(os.path.join(results_path, "skew_results_*.csv")))
bayesian_files = sorted(glob.glob(os.path.join(results_path, "bayesian_results_*.csv")))


def load_and_process(file_list, algorithm_label):
    """Loads CSVs from the found list, adds a run ID, and extracts parameters."""
    all_dfs = []
    if not file_list:
        print(f"Warning: No files found for {algorithm_label} in {results_path}")
        return pd.DataFrame()

    for i, file in enumerate(file_list):
        df = pd.read_csv(file)
        # Run_ID is based on the sorted file order (1, 2, 3, etc.)
        df['Run_ID'] = i + 1
        df['Algorithm_Type'] = algorithm_label

        # Extract numeric alpha or quantile from the Parameters string
        def get_val(p_str):
            try:
                p_dict = ast.literal_eval(p_str)
                return list(p_dict.values())[0]
            except:
                return None

        df['Param_Value'] = df['Parameters'].apply(get_val)
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)


# Combine and aggregate data
df_skew = load_and_process(skew_files, "Risk-Optimized Skew")
df_bayesian = load_and_process(bayesian_files, "Bayesian Search")
combined_df = pd.concat([df_skew, df_bayesian], ignore_index=True)

# Calculate aggregated means to find global minima
agg_stats = combined_df.groupby(['Algorithm_Type', 'Param_Value'])['Mean Guesses'].mean().reset_index()
best_skew = agg_stats[agg_stats['Algorithm_Type'] == "Risk-Optimized Skew"].sort_values('Mean Guesses').iloc[0]
best_bayesian = agg_stats[agg_stats['Algorithm_Type'] == "Bayesian Search"].sort_values('Mean Guesses').iloc[0]

# Generate plot
plt.figure(figsize=(14, 10))
sns.set_theme(style="whitegrid")

# Performance Trend Subplot
plt.subplot(2, 1, 1)
sns.lineplot(data=combined_df, x='Param_Value', y='Mean Guesses', hue='Algorithm_Type', marker='o', errorbar='sd')

# Highlight the lowest point for Skew Search
plt.scatter(best_skew['Param_Value'], best_skew['Mean Guesses'], color='red', s=120, zorder=5, label='Optimal Skew')
plt.annotate(f"Min: {best_skew['Mean Guesses']:.2f}\nAlpha: {best_skew['Param_Value']}",
             xy=(best_skew['Param_Value'], best_skew['Mean Guesses']),
             xytext=(best_skew['Param_Value']-0.08, best_skew['Mean Guesses']+8),
             arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

# Highlight the lowest point for Bayesian Search
plt.scatter(best_bayesian['Param_Value'], best_bayesian['Mean Guesses'], color='darkred', s=120, zorder=5, label='Optimal Bayesian')
plt.annotate(f"Min: {best_bayesian['Mean Guesses']:.2f}\nQuantile: {best_bayesian['Param_Value']}",
             xy=(best_bayesian['Param_Value'], best_bayesian['Mean Guesses']),
             xytext=(best_bayesian['Param_Value']-0.08, best_bayesian['Mean Guesses']+8),
             arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

plt.title('Performance Trends & Optimal Parameter Identification', fontweight='bold', fontsize=14)
plt.ylabel('Mean Guesses')
plt.legend()

# Drift Stability Subplot
plt.subplot(2, 1, 2)
sns.lineplot(data=combined_df, x='Param_Value', y='Max Drift (N)', hue='Algorithm_Type', palette=['blue', 'orange'], marker='s', errorbar='sd')
plt.title('Drift Stability Analysis', fontweight='bold', fontsize=14)
plt.ylabel('Max Drift (N)')

plt.tight_layout()
plt.savefig('results/aggregated_analysis.png', dpi=300)
print(f"Analysis complete. Found {len(skew_files)} Skew and {len(bayesian_files)} Bayesian files.")
print("Visualization saved as 'results/aggregated_analysis.png'.")
plt.show()
