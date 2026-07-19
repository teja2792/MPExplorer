"""
dimensionality_reduction.py

Three 2D embeddings of the same feature matrix from feature_engineering.py:
PCA (linear), t-SNE (nonlinear, neighborhood-preserving), UMAP (nonlinear,
neighborhood-preserving, generally better at preserving global structure
than t-SNE). All three are offered as toggleable views rather than picking
one, since they can disagree on cluster structure -- that disagreement is
itself informative, not a problem to hide.
"""

import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap


def run_pca(X, n_components=2, random_state=0):
    reducer = PCA(n_components=n_components, random_state=random_state)
    coords = reducer.fit_transform(X)
    return coords, reducer.explained_variance_ratio_


def run_tsne(X, n_components=2, perplexity=30, random_state=0):
    n_samples = X.shape[0]
    safe_perplexity = min(perplexity, max(5, (n_samples - 1) // 3))
    reducer = TSNE(n_components=n_components, perplexity=safe_perplexity,
                    random_state=random_state, init="pca")
    coords = reducer.fit_transform(X)
    return coords


def run_umap(X, n_components=2, n_neighbors=15, min_dist=0.1, random_state=0):
    n_samples = X.shape[0]
    safe_n_neighbors = min(n_neighbors, n_samples - 1)
    reducer = umap.UMAP(n_components=n_components, n_neighbors=safe_n_neighbors,
                         min_dist=min_dist, random_state=random_state)
    coords = reducer.fit_transform(X)
    return coords