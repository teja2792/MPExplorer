import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from periodic_table import build_periodic_table_figure

fig = build_periodic_table_figure(highlight_elements=["O", "Ti", "Fe", "Ce", "Cu"])

os.makedirs("results", exist_ok=True)
out_path = "results/periodic_table.html"
fig.write_html(out_path)
print(f"Saved {out_path}")