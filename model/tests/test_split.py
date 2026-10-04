from __future__ import annotations

import pandas as pd
import pytest

from leafscout_ml.split import stratified_split


def _make_clustered_df(n_clusters: int, rows_per_cluster: int, n_classes: int = 2) -> pd.DataFrame:
    rows = []
    for c in range(n_clusters):
        cls = f"class{c % n_classes}"
        for r in range(rows_per_cluster):
            rows.append({"cluster_id": c, "class_final": cls, "path_original": f"c{c}_r{r}.png"})
    return pd.DataFrame(rows)


def test_split_assigns_every_row():
    df = _make_clustered_df(n_clusters=30, rows_per_cluster=1)
    out = stratified_split(df, ratios={"train": 0.7, "val": 0.15, "test": 0.15})
    assert out["split"].notna().all()
    assert set(out["split"]) <= {"train", "val", "test"}


def test_split_keeps_clusters_together():
    df = _make_clustered_df(n_clusters=20, rows_per_cluster=3)
    out = stratified_split(df, ratios={"train": 0.7, "val": 0.15, "test": 0.15})

    for cluster_id, group in out.groupby("cluster_id"):
        assert group["split"].nunique() == 1, f"cluster {cluster_id} was split across sets"


def test_split_roughly_matches_ratios_at_scale():
    df = _make_clustered_df(n_clusters=200, rows_per_cluster=1)
    out = stratified_split(df, ratios={"train": 0.7, "val": 0.15, "test": 0.15})

    fractions = out["split"].value_counts(normalize=True)
    assert fractions["train"] == pytest.approx(0.7, abs=0.05)
    assert fractions["val"] == pytest.approx(0.15, abs=0.05)
    assert fractions["test"] == pytest.approx(0.15, abs=0.05)


def test_split_every_class_represented_in_train_even_when_tiny():
    # Classic failure mode: a class with only 2-3 clusters can get zeroed out
    # of a split by naive index-cutoff rounding. Our split must not do that.
    df = _make_clustered_df(n_clusters=6, rows_per_cluster=1, n_classes=3)  # 2 clusters/class
    out = stratified_split(df, ratios={"train": 0.7, "val": 0.15, "test": 0.15})

    train_classes = set(out[out["split"] == "train"]["class_final"])
    assert train_classes == {"class0", "class1", "class2"}


def test_split_is_deterministic_given_seed():
    df = _make_clustered_df(n_clusters=50, rows_per_cluster=2)
    out1 = stratified_split(df, seed=7)
    out2 = stratified_split(df, seed=7)
    assert list(out1["split"]) == list(out2["split"])


def test_split_rejects_ratios_not_summing_to_one():
    df = _make_clustered_df(n_clusters=10, rows_per_cluster=1)
    with pytest.raises(AssertionError):
        stratified_split(df, ratios={"train": 0.5, "val": 0.2, "test": 0.2})
