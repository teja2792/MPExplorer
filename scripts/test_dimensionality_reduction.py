import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import matplotlib.pyplot as plt
from feature_engineering import build_feature_matrix
from dimensionality_reduction import run_pca, run_tsne, run_umap

df = pd.read_csv("data/mp_summary.csv")
X_scaled, feature_names, metadata_df = build_feature_matrix(df)

pca_coords, explained_var = run_pca(X_scaled)
tsne_coords = run_tsne(X_scaled)
umap_coords = run_umap(X_scaled)

print(f"PCA explained variance (PC1, PC2): {explained_var[0]:.2f}, {explained_var[1]:.2f} "
      f"(total: {explained_var[:2].sum():.2f})")

formulas = metadata_df["formula_pretty"]
n_per_formula = formulas.value_counts()
colors = {"TiO2": "tab:blue", "Fe2O3": "tab:red", "CeO2": "tab:green", "Cu2O": "tab:orange"}

fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))

# --- PCA: axes have a real, quotable meaning ---
ax = axes[0]
for formula, color in colors.items():
    mask = formulas == formula
    ax.scatter(pca_coords[mask, 0], pca_coords[mask, 1], c=color,
               label=f"{formula} (n={n_per_formula[formula]})", s=45, alpha=0.85)
ax.set_title("PCA (linear)")
ax.set_xlabel(f"Principal Component 1\n({explained_var[0]*100:.0f}% of total variation)")
ax.set_ylabel(f"Principal Component 2\n({explained_var[1]*100:.0f}% of total variation)")
ax.legend(fontsize=8, loc="best")

# --- t-SNE and UMAP: axes are NOT physical quantities, only neighborhoods matter ---
for ax, coords, title in zip(axes[1:], [tsne_coords, umap_coords], ["t-SNE", "UMAP"]):
    for formula, color in colors.items():
        mask = formulas == formula
        ax.scatter(coords[mask, 0], coords[mask, 1], c=color,
                   label=f"{formula} (n={n_per_formula[formula]})", s=45, alpha=0.85)
    ax.set_title(title)
    ax.set_xlabel(f"{title} axis 1\n(no physical meaning -- only closeness matters)")
    ax.set_ylabel(f"{title} axis 2\n(no physical meaning -- only closeness matters)")

fig.suptitle(
    "How the 77 Materials Project entries group by their computed properties\n"
    "Caution: CeO2 (n=4) and Cu2O (n=1) are too few points for t-SNE/UMAP placement to be reliable -- "
    "notice the three methods disagree on where they belong",
    fontsize=10,
)
fig.tight_layout(rect=[0, 0, 1, 0.90])

os.makedirs("results", exist_ok=True)
fig.savefig("results/dim_reduction_comparison.png", dpi=150)
print("Saved results/dim_reduction_comparison.png")