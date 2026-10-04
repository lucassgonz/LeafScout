"""Cluster-safe, class-stratified train/val/test split.

A duplicate cluster (see dedup.py) is assigned to exactly one split — never
split across train and test — otherwise accuracy numbers would be inflated
by near-identical images leaking between train and evaluation.
"""
from __future__ import annotations

import random

import pandas as pd

from .config import RANDOM_SEED, SPLIT_RATIOS


def stratified_split(
    df: pd.DataFrame,
    ratios: dict[str, float] = SPLIT_RATIOS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Assign a ``split`` column, keeping every cluster_id together.

    Stratifies at the cluster level by the cluster's majority class, so each
    split keeps roughly the same class balance as the full dataset.
    """
    assert abs(sum(ratios.values()) - 1.0) < 1e-6, "split ratios must sum to 1.0"

    df = df.copy()
    rng = random.Random(seed)

    # One representative class per cluster (majority vote; clusters are
    # near-duplicates so they're virtually always single-class anyway).
    cluster_class = (
        df.groupby("cluster_id")["class_final"]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )

    # Group clusters by their representative class, shuffle deterministically,
    # then walk each class's cluster list assigning to splits by running ratio.
    clusters_by_class: dict[str, list[int]] = {}
    for cluster_id, cls in cluster_class.items():
        clusters_by_class.setdefault(cls, []).append(cluster_id)

    split_names = list(ratios.keys())
    cluster_split: dict[int, str] = {}

    for cls, cluster_ids in clusters_by_class.items():
        cluster_ids = sorted(cluster_ids)  # deterministic order before shuffle
        rng.shuffle(cluster_ids)
        n = len(cluster_ids)
        counts = {name: 0 for name in split_names}
        cursor = 0
        # Assign clusters one at a time to whichever split is furthest below
        # its target ratio, so small classes still get every split represented
        # when n is small (plain index-cutoff rounding can zero out a split).
        for cluster_id in cluster_ids:
            deficits = {
                name: ratios[name] * (cursor + 1) - counts[name] for name in split_names
            }
            chosen = max(deficits, key=deficits.get)
            cluster_split[cluster_id] = chosen
            counts[chosen] += 1
            cursor += 1

    df["split"] = df["cluster_id"].map(cluster_split)
    return df
