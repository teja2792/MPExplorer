import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from crystal_viewer import build_structure_figure

STABLE_IDS = {
    "TiO2 (anatase)": "mp-390",
    "Fe2O3 (hematite)": "mp-19770",
    "CeO2 (fluorite)": "mp-20194",
    "Cu2O (cuprite)": "mp-361",
}

os.makedirs("results/structures", exist_ok=True)
for label, mid in STABLE_IDS.items():
    fig = build_structure_figure(mid)
    out_path = f"results/structures/{mid}.html"
    fig.write_html(out_path)
    print(f"{label} ({mid}): saved to {out_path}")