import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from mp_client import search_multiple_formulas

TARGET_FORMULAS = ["TiO2", "Fe2O3", "CeO2", "Cu2O"]

df = search_multiple_formulas(TARGET_FORMULAS)

os.makedirs("data", exist_ok=True)
out_path = "data/mp_summary.csv"
df.to_csv(out_path, index=False)

print(f"Pulled {len(df)} total entries across {len(TARGET_FORMULAS)} formulas.")
print(df["formula_pretty"].value_counts())
print()
print("DFT methodology breakdown:")
print(df["dft_run_type"].value_counts(dropna=False))
print()
print("Data completeness (% non-null per column, overall):")
print((df.notna().mean() * 100).round(1))
print()
print("Elastic modulus coverage BY MATERIAL (bulk_modulus_GPa non-null):")
for formula in TARGET_FORMULAS:
    sub = df[df["formula_pretty"] == formula]
    n_total = len(sub)
    n_have = sub["bulk_modulus_GPa"].notna().sum()
    pct = 100 * n_have / n_total if n_total else 0
    print(f"  {formula}: {n_have}/{n_total} entries ({pct:.0f}%)")
print()
print(f"Saved to {out_path}")