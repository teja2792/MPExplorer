"""
feature_engineering.py

Builds a numeric feature matrix from the Materials Project summary data
for use in PCA/UMAP/t-SNE (Phase 4 visualization).

Deliberately uses only the columns that are 100% complete across all 77
entries (band_gap_eV, formation_energy_per_atom_eV, density_g_cm3,
crystal_system, is_stable, dft_run_type). Bulk/shear modulus are excluded
here because they're only ~23% populated -- imputing the missing 77%
would manufacture fake structure in a PCA/UMAP/t-SNE plot. They can be
layered on later as an optional overlay for the subset that has them.
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

NUMERIC_FEATURES = ["band_gap_eV", "formation_energy_per_atom_eV", "density_g_cm3"]
CATEGORICAL_FEATURES = ["crystal_system", "dft_run_type"]
BOOLEAN_FEATURES = ["is_stable"]


def build_feature_matrix(df: pd.DataFrame):
    """
    Returns (X_scaled, feature_names, metadata_df).
    metadata_df carries formula_pretty/material_id/is_stable/dft_run_type
    alongside each row for coloring/labeling plots later -- it is NOT part
    of the feature matrix itself.
    """
    work = df.copy()
    work["is_stable_int"] = work["is_stable"].astype(int)

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ("bool", "passthrough", ["is_stable_int"]),
    ])

    X_scaled = preprocessor.fit_transform(work)
    feature_names = preprocessor.get_feature_names_out()

    metadata_df = work[["material_id", "formula_pretty", "is_stable",
                         "dft_run_type", "space_group_symbol"]].reset_index(drop=True)

    return X_scaled, feature_names, metadata_df