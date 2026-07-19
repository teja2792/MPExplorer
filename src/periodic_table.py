"""
periodic_table.py

Builds a full periodic-table-shaped plotly figure, colored by elemental
Pauling electronegativity (a real, standard, universally-available
elemental property, distinct from the compound-specific DFT properties
used elsewhere in this repo). The five elements actually present in this
repo's target compounds (O, Ti, Fe, Ce, Cu) are outlined so they're easy
to spot against the full table.

Layout (period, group) is hand-coded rather than pulled from a library
attribute, since it's fixed chemistry knowledge, not an API surface that
can shift between library versions.
"""

import plotly.graph_objects as go
from pymatgen.core.periodic_table import Element

# (symbol, period, group) -- lanthanides/actinides placed in rows 9/10,
# groups 4-17, the standard simplified textbook layout.
_LAYOUT = [
    ("H", 1, 1), ("He", 1, 18),
    ("Li", 2, 1), ("Be", 2, 2), ("B", 2, 13), ("C", 2, 14), ("N", 2, 15), ("O", 2, 16), ("F", 2, 17), ("Ne", 2, 18),
    ("Na", 3, 1), ("Mg", 3, 2), ("Al", 3, 13), ("Si", 3, 14), ("P", 3, 15), ("S", 3, 16), ("Cl", 3, 17), ("Ar", 3, 18),
    ("K", 4, 1), ("Ca", 4, 2), ("Sc", 4, 3), ("Ti", 4, 4), ("V", 4, 5), ("Cr", 4, 6), ("Mn", 4, 7), ("Fe", 4, 8),
    ("Co", 4, 9), ("Ni", 4, 10), ("Cu", 4, 11), ("Zn", 4, 12), ("Ga", 4, 13), ("Ge", 4, 14), ("As", 4, 15),
    ("Se", 4, 16), ("Br", 4, 17), ("Kr", 4, 18),
    ("Rb", 5, 1), ("Sr", 5, 2), ("Y", 5, 3), ("Zr", 5, 4), ("Nb", 5, 5), ("Mo", 5, 6), ("Tc", 5, 7), ("Ru", 5, 8),
    ("Rh", 5, 9), ("Pd", 5, 10), ("Ag", 5, 11), ("Cd", 5, 12), ("In", 5, 13), ("Sn", 5, 14), ("Sb", 5, 15),
    ("Te", 5, 16), ("I", 5, 17), ("Xe", 5, 18),
    ("Cs", 6, 1), ("Ba", 6, 2), ("La", 6, 3), ("Hf", 6, 4), ("Ta", 6, 5), ("W", 6, 6), ("Re", 6, 7), ("Os", 6, 8),
    ("Ir", 6, 9), ("Pt", 6, 10), ("Au", 6, 11), ("Hg", 6, 12), ("Tl", 6, 13), ("Pb", 6, 14), ("Bi", 6, 15),
    ("Po", 6, 16), ("At", 6, 17), ("Rn", 6, 18),
    ("Fr", 7, 1), ("Ra", 7, 2), ("Ac", 7, 3), ("Rf", 7, 4), ("Db", 7, 5), ("Sg", 7, 6), ("Bh", 7, 7), ("Hs", 7, 8),
    ("Mt", 7, 9), ("Ds", 7, 10), ("Rg", 7, 11), ("Cn", 7, 12), ("Nh", 7, 13), ("Fl", 7, 14), ("Mc", 7, 15),
    ("Lv", 7, 16), ("Ts", 7, 17), ("Og", 7, 18),
    ("Ce", 9, 4), ("Pr", 9, 5), ("Nd", 9, 6), ("Pm", 9, 7), ("Sm", 9, 8), ("Eu", 9, 9), ("Gd", 9, 10),
    ("Tb", 9, 11), ("Dy", 9, 12), ("Ho", 9, 13), ("Er", 9, 14), ("Tm", 9, 15), ("Yb", 9, 16), ("Lu", 9, 17),
    ("Th", 10, 4), ("Pa", 10, 5), ("U", 10, 6), ("Np", 10, 7), ("Pu", 10, 8), ("Am", 10, 9), ("Cm", 10, 10),
    ("Bk", 10, 11), ("Cf", 10, 12), ("Es", 10, 13), ("Fm", 10, 14), ("Md", 10, 15), ("No", 10, 16), ("Lr", 10, 17),
]


def build_periodic_table_figure(highlight_elements=None):
    highlight_elements = set(highlight_elements or [])

    symbols, xs, ys, values, line_widths, line_colors = [], [], [], [], [], []
    for symbol, period, group in _LAYOUT:
        try:
            X = Element(symbol).X  # Pauling electronegativity; None for some elements
        except Exception:
            X = None
        symbols.append(symbol)
        xs.append(group)
        ys.append(-period)  # negative so period 1 renders at the top
        values.append(X)
        is_highlighted = symbol in highlight_elements
        line_widths.append(3 if is_highlighted else 0.5)
        line_colors.append("black" if is_highlighted else "lightgray")

    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        text=symbols, textposition="middle center",
        marker=dict(
            symbol="square", size=32,
            color=values, colorscale="Viridis",
            colorbar=dict(title="Electronegativity\n(Pauling scale)"),
            showscale=True,
            line=dict(width=line_widths, color=line_colors),
        ),
        hovertext=[f"{s}: X={v}" if v is not None else f"{s}: no data" for s, v in zip(symbols, values)],
        hoverinfo="text",
    ))

    fig.update_layout(
        title="Periodic table colored by electronegativity"
              + (f"  (outlined: {', '.join(sorted(highlight_elements))} -- present in this repo's compounds)"
                 if highlight_elements else ""),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=550,
        plot_bgcolor="white",
    )
    return fig