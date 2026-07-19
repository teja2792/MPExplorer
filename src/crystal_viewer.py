"""
crystal_viewer.py

Builds an interactive 3D plotly figure of a crystal structure fetched
directly from Materials Project by material_id: atoms as colored points,
unit cell edges as lines. Element colors are a simplified, Jmol-inspired
palette for visualization only -- not a scientifically standardized
color convention, and not claimed to be one.

Assumes ordered structures (single species per site), true for all four
target materials here. A disordered/partial-occupancy structure would
need site.species instead of site.specie -- not handled, out of scope.
"""

import os
import itertools
import numpy as np
import plotly.graph_objects as go
from mp_api.client import MPRester

ELEMENT_COLORS = {
    "O": "#FF0D0D",
    "Ti": "#BFC2C7",
    "Fe": "#E06633",
    "Ce": "#C7B000",
    "Cu": "#C88033",
    "Pd": "#006985",
    "Au": "#FFD123",
    "Ag": "#C0C0C0",
}
DEFAULT_COLOR = "#8A8A8A"


def _get_api_key(api_key=None):
    key = api_key or os.environ.get("MP_API_KEY")
    if not key:
        raise RuntimeError('MP_API_KEY not set.')
    return key


def _unit_cell_edges(lattice_matrix):
    a, b, c = np.array(lattice_matrix)
    corners = {}
    for i, j, k in itertools.product([0, 1], repeat=3):
        corners[(i, j, k)] = i * a + j * b + k * c

    edges = []
    for (i, j, k), point in corners.items():
        for axis in range(3):
            neighbor = [i, j, k]
            if neighbor[axis] == 0:
                neighbor[axis] = 1
                neighbor = tuple(neighbor)
                edges.append((point, corners[neighbor]))
    return edges


def build_structure_figure(material_id: str, api_key: str = None) -> go.Figure:
    key = _get_api_key(api_key)
    with MPRester(key) as mpr:
        structure = mpr.get_structure_by_material_id(material_id)

    fig = go.Figure()

    edges = _unit_cell_edges(structure.lattice.matrix)
    for start, end in edges:
        fig.add_trace(go.Scatter3d(
            x=[start[0], end[0]], y=[start[1], end[1]], z=[start[2], end[2]],
            mode="lines", line=dict(color="black", width=2),
            showlegend=False, hoverinfo="skip",
        ))

    elements_present = sorted(set(str(site.specie) for site in structure.sites))
    for element in elements_present:
        coords = np.array([site.coords for site in structure.sites if str(site.specie) == element])
        fig.add_trace(go.Scatter3d(
            x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
            mode="markers",
            marker=dict(size=10, color=ELEMENT_COLORS.get(element, DEFAULT_COLOR)),
            name=element,
        ))

    fig.update_layout(
        title=f"{material_id}: {structure.composition.reduced_formula} "
              f"({structure.get_space_group_info()[0]})",
        scene=dict(
            xaxis_title="x (Angstrom)",
            yaxis_title="y (Angstrom)",
            zaxis_title="z (Angstrom)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )
    return fig