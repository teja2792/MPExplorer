import os
from mp_api.client import MPRester

api_key = os.environ.get("MP_API_KEY")
if not api_key:
    raise RuntimeError("MP_API_KEY environment variable not set. Restart your terminal after running setx.")

with MPRester(api_key) as mpr:
    docs = mpr.materials.summary.search(formula="TiO2", fields=["material_id", "formula_pretty", "band_gap"])

print(f"Connected successfully. Found {len(docs)} TiO2 entries.")
for d in docs[:5]:
    print(f"  {d.material_id}: {d.formula_pretty}, band_gap = {d.band_gap} eV")