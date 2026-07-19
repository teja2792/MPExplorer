"""
mp_client.py

Thin wrapper around the Materials Project API for pulling summary
properties for one or more chemical formulas, merged with the DFT
methodology (energy_type: GGA vs. GGA+U vs. r2SCAN) used for each entry.

Why this matters: GGA band gaps are systematically underestimated by
~40% on average (Materials Project's own documented figure). Materials
Project applies a Hubbard U correction (GGA+U) only to a specific list of
transition metals with known self-interaction problems: Fe, Mn, Co, Cr,
Ni, V. Ce is NOT on that list -- confirmed empirically here, since all 4
CeO2 entries in this dataset come back tagged plain GGA with no
Hubbard-corrected alternative available. That matters: Ce 4f electrons
are a textbook severe self-interaction-error case, and this dataset's
plain-GGA CeO2 entries range from 0.0 eV (predicted as a metal) to 2.15
eV, against an experimental range of 2.6-3.9 eV -- a larger, partly
qualitative failure, not just the "typical" ~40% quantitative one.
Tracking energy_type per entry lets the rest of this repo report all of
this honestly instead of treating every entry as equally reliable.
"""

import os
import pandas as pd
from mp_api.client import MPRester

SUMMARY_FIELDS = [
    "material_id",
    "formula_pretty",
    "band_gap",
    "formation_energy_per_atom",
    "density",
    "symmetry",
    "is_stable",
]


def _get_api_key(api_key=None):
    key = api_key or os.environ.get("MP_API_KEY")
    if not key:
        raise RuntimeError('MP_API_KEY not set. Run \'setx MP_API_KEY "your_key"\' '
                            "and restart your terminal.")
    return key


def search_formula(formula: str, api_key: str = None) -> pd.DataFrame:
    """
    Returns one row per polymorph/entry matching `formula`, with summary
    properties and the DFT methodology (energy_type: GGA / GGA+U / r2SCAN,
    plus the full list of available_functionals per material) merged in.
    """
    key = _get_api_key(api_key)

    with MPRester(key) as mpr:
        docs = mpr.materials.summary.search(formula=formula, fields=SUMMARY_FIELDS)

        rows = []
        for d in docs:
            rows.append({
                "material_id": str(d.material_id),
                "formula_pretty": d.formula_pretty,
                "band_gap_eV": d.band_gap,
                "formation_energy_per_atom_eV": d.formation_energy_per_atom,
                "density_g_cm3": d.density,
                "space_group_symbol": d.symmetry.symbol if d.symmetry else None,
                "crystal_system": str(d.symmetry.crystal_system) if d.symmetry else None,
                "is_stable": d.is_stable,
            })

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        material_ids = df["material_id"].tolist()
        thermo_docs = mpr.materials.thermo.search(
            material_ids=material_ids, fields=["material_id", "energy_type", "entry_types"]
        )
        run_type_map = {}
        entry_types_map = {}
        for t in thermo_docs:
            mid = str(t.material_id)
            run_type_map[mid] = str(t.energy_type)
            entry_types_map[mid] = ", ".join(str(e) for e in t.entry_types) if t.entry_types else None

        df["dft_run_type"] = df["material_id"].map(run_type_map)
        df["available_functionals"] = df["material_id"].map(entry_types_map)

    return df


def search_multiple_formulas(formulas: list, api_key: str = None) -> pd.DataFrame:
    frames = [search_formula(f, api_key=api_key) for f in formulas]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True)