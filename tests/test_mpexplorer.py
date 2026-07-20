"""
tests/test_mpexplorer.py

Two groups of tests:
  1. Tests against the committed data/mp_summary.csv snapshot -- fast,
     deterministic, no network required. These also lock in the specific,
     verified findings from this repo's build process (Fe2O3 is all
     GGA+U, the analytical feature-matrix shape, etc.) as regression tests.
  2. Tests that hit the live Materials Project API -- automatically
     skipped if MP_API_KEY isn't set, rather than failing the whole suite
     when run somewhere without network/credentials.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from feature_engineering import build_feature_matrix
from dimensionality_reduction import run_pca, run_tsne, run_umap
from periodic_table import _LAYOUT, build_periodic_table_figure
from crystal_viewer import _unit_cell_edges
from band_gap_reference import build_comparison_table

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mp_summary.csv")
requires_api_key = pytest.mark.skipif(
    not os.environ.get("MP_API_KEY"), reason="MP_API_KEY not set -- skipping live API tests"
)


@pytest.fixture
def df():
    return pd.read_csv(DATA_PATH)


# --- Data snapshot regression tests ---

def test_dataset_has_four_formulas_with_expected_counts(df):
    counts = df["formula_pretty"].value_counts().to_dict()
    assert counts == {"TiO2": 46, "Fe2O3": 26, "CeO2": 4, "Cu2O": 1}


def test_fe2o3_entries_are_all_gga_u(df):
    """Regression test locking in the verified finding: every Fe2O3 entry
    in this snapshot uses the Hubbard-U correction (Fe is on MP's
    standard U-correction element list)."""
    fe2o3 = df[df["formula_pretty"] == "Fe2O3"]
    assert (fe2o3["dft_run_type"] == "GGA+U").all()


def test_ceo2_entries_are_all_plain_gga(df):
    """Regression test locking in the corrected finding: Ce is NOT on
    MP's standard U-correction list, unlike the (wrong) claim this repo
    initially made before checking the live data."""
    ceo2 = df[df["formula_pretty"] == "CeO2"]
    assert (ceo2["dft_run_type"] == "GGA").all()


def test_only_one_fe2o3_entry_is_stable(df):
    fe2o3 = df[df["formula_pretty"] == "Fe2O3"]
    assert fe2o3["is_stable"].sum() == 1


# --- Feature engineering / dimensionality reduction ---

def test_feature_matrix_shape_and_no_missing_values(df):
    X_scaled, feature_names, metadata_df = build_feature_matrix(df)
    assert X_scaled.shape == (77, 14)
    assert not np.isnan(X_scaled).any(), (
        "Feature matrix must never contain NaN -- this repo deliberately "
        "excludes sparse columns (bulk/shear modulus) rather than impute them."
    )


def test_pca_explained_variance_is_decreasing_and_valid(df):
    X_scaled, _, _ = build_feature_matrix(df)
    coords, explained_var = run_pca(X_scaled)
    assert coords.shape == (77, 2)
    assert explained_var[0] >= explained_var[1]
    assert 0 < explained_var[:2].sum() <= 1.0


def test_tsne_and_umap_produce_valid_shapes(df):
    X_scaled, _, _ = build_feature_matrix(df)
    tsne_coords = run_tsne(X_scaled)
    umap_coords = run_umap(X_scaled)
    assert tsne_coords.shape == (77, 2)
    assert umap_coords.shape == (77, 2)


# --- Periodic table ---

def test_periodic_table_positions_for_dataset_elements():
    layout_dict = {symbol: (period, group) for symbol, period, group in _LAYOUT}
    assert layout_dict["Ti"] == (4, 4)
    assert layout_dict["Fe"] == (4, 8)
    assert layout_dict["Cu"] == (4, 11)
    assert layout_dict["O"] == (2, 16)
    assert layout_dict["Ce"] == (9, 4)


def test_periodic_table_figure_builds_without_error():
    fig = build_periodic_table_figure(highlight_elements=["O", "Ti", "Fe", "Ce", "Cu"])
    assert fig is not None
    assert len(fig.data) >= 1


# --- Crystal viewer geometry (no API call needed) ---

def test_unit_cell_edges_count_for_cubic_lattice():
    cubic_lattice = [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]]
    edges = _unit_cell_edges(cubic_lattice)
    assert len(edges) == 12  # a cube has exactly 12 edges, each counted once


# --- Band gap methodology table ---

def test_band_gap_comparison_table_matches_verified_findings():
    table = build_comparison_table()
    assert set(table["formula"]) == {"TiO2", "Fe2O3", "CeO2", "Cu2O"}

    fe2o3_row = table[table["formula"] == "Fe2O3"].iloc[0]
    assert fe2o3_row["dft_band_gap_eV"] == 0.0
    assert "METAL" in fe2o3_row["failure_mode"]

    tio2_row = table[table["formula"] == "TiO2"].iloc[0]
    assert "anatase" in tio2_row["mp_stable_phase"]
    assert "WRONG STABLE POLYMORPH" in tio2_row["failure_mode"]


# --- Live API tests (skipped without MP_API_KEY) ---

@requires_api_key
def test_live_cu2o_search_returns_single_known_entry():
    from mp_client import search_formula
    result = search_formula("Cu2O")
    assert len(result) == 1
    assert result.iloc[0]["material_id"] == "mp-361"


@requires_api_key
def test_live_crystal_structure_fetch_builds_figure():
    from crystal_viewer import build_structure_figure
    fig = build_structure_figure("mp-361")
    assert len(fig.data) >= 2  # at least one unit-cell-edge trace + one atom trace