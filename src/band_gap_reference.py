"""
band_gap_reference.py

Phase 3: compares each material's Materials-Project-identified stable
polymorph against literature experimental band gap values, documenting
the SPECIFIC, verified DFT failure mode for each -- not a single blanket
"GGA is off by 40%" statement, because the failure mode differs for every
one of these four materials. No blanket correction factor is applied
anywhere in this repo. This table lets a user see the raw DFT number next
to the real experimental value and the documented reason they differ, for
exactly the four materials this repo covers.

If more materials are added later, this table must be extended manually
with verified literature values -- accuracy over automation, deliberately.
"""

import os
import pandas as pd

EXPERIMENTAL_REFERENCE = [
    {
        "formula": "TiO2",
        "mp_stable_id": "mp-390",
        "mp_stable_phase": "anatase (I4_1/amd)",
        "dft_band_gap_eV": 2.06,
        "dft_run_type": "GGA",
        "true_experimental_ground_state": "rutile (NOT anatase)",
        "experimental_gap_range_eV": "3.0 (rutile) - 3.2 (anatase), indirect",
        "failure_mode": "WRONG STABLE POLYMORPH -- GGA/PBE is documented to "
                         "over-stabilize anatase relative to rutile; the true "
                         "experimental ground state is rutile, not what MP's "
                         "DFT identifies as most stable.",
    },
    {
        "formula": "Fe2O3",
        "mp_stable_id": "mp-19770",
        "mp_stable_phase": "hematite (R-3c)",
        "dft_band_gap_eV": 0.0,
        "dft_run_type": "GGA+U",
        "true_experimental_ground_state": "hematite (correctly identified)",
        "experimental_gap_range_eV": "2.0 - 2.2 (direct ~2.1-2.2, indirect ~1.5-1.9)",
        "failure_mode": "QUALITATIVE FAILURE -- predicted as a METAL (0.0 eV) "
                         "despite the Hubbard-U correction specifically applied "
                         "to Fe for this self-interaction problem. Real hematite "
                         "is a well-known semiconductor.",
    },
    {
        "formula": "CeO2",
        "mp_stable_id": "mp-20194",
        "mp_stable_phase": "fluorite (Fm-3m)",
        "dft_band_gap_eV": 2.00,
        "dft_run_type": "GGA",
        "true_experimental_ground_state": "fluorite (correctly identified)",
        "experimental_gap_range_eV": "2.6 - 3.9 (wide literature spread)",
        "failure_mode": "QUANTITATIVE UNDERESTIMATE -- no Hubbard correction "
                         "available for Ce in MP's standard scheme (only Fe, "
                         "Mn, Co, Cr, Ni, V are covered); Ce 4f self-interaction "
                         "error is a well-documented severe case in the "
                         "literature.",
    },
    {
        "formula": "Cu2O",
        "mp_stable_id": "mp-361",
        "mp_stable_phase": "cuprite (Pn-3m)",
        "dft_band_gap_eV": 0.51,
        "dft_run_type": "GGA",
        "true_experimental_ground_state": "cuprite (correctly identified)",
        "experimental_gap_range_eV": "2.1 - 2.2 (direct-forbidden ~2.17)",
        "failure_mode": "LARGE QUANTITATIVE UNDERESTIMATE -- ~75% below the "
                         "experimental value, the worst quantitative miss of "
                         "the four. This is the compound this repo's author's "
                         "own published photocatalysis work is built on.",
    },
]


def build_comparison_table() -> pd.DataFrame:
    return pd.DataFrame(EXPERIMENTAL_REFERENCE)


if __name__ == "__main__":
    df = build_comparison_table()
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.width", 200)
    print(df[["formula", "mp_stable_phase", "dft_band_gap_eV", "dft_run_type",
              "experimental_gap_range_eV"]].to_string(index=False))
    print()
    for _, row in df.iterrows():
        print(f"{row['formula']}: {row['failure_mode']}")
        print()

    os.makedirs("results", exist_ok=True)
    df.to_csv("results/band_gap_methodology_comparison.csv", index=False)
    print("Saved results/band_gap_methodology_comparison.csv")