"""
app.py

MPExplorer -- Streamlit app tying together Search, Download, and Visualize
(Crystal / Periodic Table / PCA / UMAP / t-SNE) over Materials Project
data for TiO2, Fe2O3, CeO2, Cu2O (extensible to any formula via live query).
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd

from mp_client import search_multiple_formulas
from feature_engineering import build_feature_matrix
from dimensionality_reduction import run_pca, run_tsne, run_umap
from crystal_viewer import build_structure_figure
from periodic_table import build_periodic_table_figure
from band_gap_reference import build_comparison_table

st.set_page_config(page_title="MPExplorer", layout="wide")
st.title("MPExplorer")
st.caption("A Materials Project explorer for TiO2, Fe2O3, CeO2, Cu2O -- with DFT methodology "
           "caveats surfaced explicitly rather than hidden.")

DATA_PATH = "data/mp_summary.csv"


@st.cache_data
def load_base_data():
    return pd.read_csv(DATA_PATH)


if "working_df" not in st.session_state:
    st.session_state.working_df = load_base_data()

df = st.session_state.working_df

# --- Sidebar: Search ---
st.sidebar.header("Search")
all_formulas = sorted(df["formula_pretty"].unique())
selected_formulas = st.sidebar.multiselect("Formulas to include", all_formulas, default=all_formulas)

st.sidebar.markdown("---")
st.sidebar.subheader("Add a new formula (live query)")
new_formula = st.sidebar.text_input("Formula (e.g. SnO2)")
if st.sidebar.button("Fetch from Materials Project"):
    if not os.environ.get("MP_API_KEY"):
        st.sidebar.error("MP_API_KEY not set in this environment.")
    elif not new_formula:
        st.sidebar.warning("Enter a formula first.")
    else:
        with st.spinner(f"Querying Materials Project for {new_formula}..."):
            try:
                new_df = search_multiple_formulas([new_formula])
                st.session_state.working_df = pd.concat(
                    [st.session_state.working_df, new_df], ignore_index=True
                ).drop_duplicates(subset="material_id")
                st.sidebar.success(f"Added {len(new_df)} entries for {new_formula}.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Query failed: {e}")

filtered_df = df[df["formula_pretty"].isin(selected_formulas)].reset_index(drop=True)

tab_search, tab_crystal, tab_periodic, tab_dimred, tab_methodology = st.tabs(
    ["Search & Download", "Crystal Structure", "Periodic Table", "PCA / UMAP / t-SNE", "Methodology & Caveats"]
)

# --- Tab 1: Search & Download ---
with tab_search:
    st.subheader(f"{len(filtered_df)} entries across {len(selected_formulas)} formula(s)")

    all_columns = list(filtered_df.columns)
    default_columns = ["material_id", "formula_pretty", "band_gap_eV", "formation_energy_per_atom_eV",
                        "density_g_cm3", "space_group_symbol", "is_stable", "dft_run_type"]
    selected_columns = st.multiselect("Properties to show/download", all_columns,
                                       default=[c for c in default_columns if c in all_columns])

    if selected_columns:
        display_df = filtered_df[selected_columns]
        st.dataframe(display_df, width="stretch")
        st.download_button(
            "Download as CSV",
            display_df.to_csv(index=False).encode("utf-8"),
            file_name="mpexplorer_export.csv",
            mime="text/csv",
        )
    else:
        st.info("Select at least one property to display.")

# --- Tab 2: Crystal Structure ---
with tab_crystal:
    st.subheader("3D crystal structure viewer")
    st.caption("Requires a live Materials Project query -- full structures aren't cached locally.")

    stable_first = filtered_df.sort_values("is_stable", ascending=False)
    options = stable_first["material_id"] + " -- " + stable_first["formula_pretty"] + \
        stable_first["is_stable"].map({True: " (stable)", False: " (hypothetical)"})

    if len(options) == 0:
        st.info("No entries available for the selected formulas.")
    else:
        choice = st.selectbox("Select an entry", options)
        material_id = choice.split(" -- ")[0]

        if not os.environ.get("MP_API_KEY"):
            st.error("MP_API_KEY not set in this environment.")
        else:
            with st.spinner(f"Fetching structure for {material_id}..."):
                try:
                    fig = build_structure_figure(material_id)
                    st.plotly_chart(fig, width="stretch")
                except Exception as e:
                    st.error(f"Failed to fetch structure: {e}")

# --- Tab 3: Periodic Table ---
with tab_periodic:
    st.subheader("Periodic table (electronegativity)")
    formula_elements = {
        "TiO2": ["Ti", "O"], "Fe2O3": ["Fe", "O"], "CeO2": ["Ce", "O"], "Cu2O": ["Cu", "O"],
    }
    elements_in_view = set()
    for formula in selected_formulas:
        elements_in_view.update(formula_elements.get(formula, []))

    fig = build_periodic_table_figure(highlight_elements=elements_in_view)
    st.plotly_chart(fig, width="stretch")

# --- Tab 4: PCA / UMAP / t-SNE ---
with tab_dimred:
    st.subheader("Property-space visualization")
    st.caption("Built from computed properties (band gap, formation energy, density, crystal system, "
               "stability, DFT method) -- NOT composition alone, since only 4 unique formulas would make "
               "composition-based clustering trivial.")

    MIN_SAMPLES = 5
    if len(filtered_df) < MIN_SAMPLES:
        st.warning(f"Select at least {MIN_SAMPLES} entries (across one or more formulas) to run "
                   f"dimensionality reduction. Currently: {len(filtered_df)}.")
    else:
        method = st.radio("Method", ["PCA (linear)", "t-SNE", "UMAP"], horizontal=True)
        X_scaled, feature_names, metadata_df = build_feature_matrix(filtered_df)

        if method == "PCA (linear)":
            coords, explained_var = run_pca(X_scaled)
            st.caption(f"PC1 explains {explained_var[0]*100:.0f}% of variation, "
                       f"PC2 explains {explained_var[1]*100:.0f}% (total {explained_var[:2].sum()*100:.0f}%).")
        elif method == "t-SNE":
            coords = run_tsne(X_scaled)
            st.caption("Axes have no physical meaning -- only relative closeness matters.")
        else:
            coords = run_umap(X_scaled)
            st.caption("Axes have no physical meaning -- only relative closeness matters.")

        plot_df = pd.DataFrame({
            "Dim 1": coords[:, 0], "Dim 2": coords[:, 1],
            "Formula": metadata_df["formula_pretty"],
            "Stable": metadata_df["is_stable"],
            "DFT method": metadata_df["dft_run_type"],
            "Material ID": metadata_df["material_id"],
        })
        import plotly.express as px
        fig = px.scatter(plot_df, x="Dim 1", y="Dim 2", color="Formula", symbol="Stable",
                          hover_data=["Material ID", "DFT method"])
        st.plotly_chart(fig, width="stretch")

        small_groups = [f for f in selected_formulas if (filtered_df["formula_pretty"] == f).sum() < 5]
        if small_groups:
            st.info(f"Caution: {', '.join(small_groups)} have fewer than 5 entries -- their placement "
                    f"in this plot (especially for t-SNE/UMAP) shouldn't be over-interpreted.")

# --- Tab 5: Methodology & Caveats ---
with tab_methodology:
    st.subheader("DFT methodology comparison: raw values vs. literature")
    st.caption("Every material fails differently -- not a single blanket correction factor.")
    comparison_df = build_comparison_table()
    st.dataframe(comparison_df, width="stretch")

    st.markdown("""
**Key caveats this repo surfaces rather than hides:**
- Materials Project applies a Hubbard-U correction (GGA+U) only to Fe, Mn, Co, Cr, Ni, V --
  not Ce, despite Ce having a comparably severe self-interaction problem.
- Elastic modulus data covers only ~23% of entries in this dataset, and coverage is
  uncorrelated with which entry is the real, stable material (Fe2O3: 0% coverage,
  including its one real stable structure).
- Of Fe2O3's 26 computed entries, only 1 is thermodynamically stable; the other 25 are
  hypothetical structures generated by Materials Project's substitution algorithm.
- TiO2's DFT-predicted stable polymorph is anatase, not rutile -- a documented GGA/PBE
  artifact, not a data error.
- No blanket band-gap correction factor is applied anywhere in this app.
""")