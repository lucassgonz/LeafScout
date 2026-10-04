"""Cross-source deduplication: exact (MD5) and near-duplicate (pHash) clustering.

Prevents the same (or near-identical) photo from appearing in both train and
test after fusing multiple public sources — a real risk here since BRACOL,
the Tanzania/Bangladesh bean sets, PlantVillage and PlantDoc occasionally
share or re-crop the same underlying photographs.
"""
from __future__ import annotations

import pandas as pd

from .config import PHASH_HAMMING_THRESHOLD


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _hamming(a: str, b: str) -> int:
    # phash strings are hex digests of equal length; compare as integers.
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def dedup(manifest: pd.DataFrame, phash_threshold: int = PHASH_HAMMING_THRESHOLD) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cluster exact + near-duplicate images.

    Returns ``(manifest_with_cluster_id, duplicates_report)``. Every row keeps
    its own line (nothing is dropped here — that's the split stage's job);
    rows sharing a ``cluster_id`` MUST end up in the same split.
    """
    df = manifest.reset_index(drop=True).copy()
    n = len(df)
    uf = _UnionFind(n)

    # Exact duplicates: same MD5 anywhere (within or across sources).
    for _, group in df.groupby("md5").groups.items():
        idxs = list(group)
        for other in idxs[1:]:
            uf.union(idxs[0], other)

    # Near-duplicates: pHash Hamming distance <= threshold.
    # O(n^2) is fine at the hackathon's dataset scale (low thousands of images);
    # revisit with a BK-tree / LSH if a crop's fused set grows past ~20k images.
    has_phash = df["phash"].notna()
    phash_idx = df.index[has_phash].tolist()
    phashes = df.loc[phash_idx, "phash"].tolist()
    for i in range(len(phash_idx)):
        for j in range(i + 1, len(phash_idx)):
            if _hamming(phashes[i], phashes[j]) <= phash_threshold:
                uf.union(phash_idx[i], phash_idx[j])

    cluster_ids = [uf.find(i) for i in range(n)]
    df["cluster_id"] = cluster_ids

    # Report: clusters with more than one member, and which sources they span.
    dup_rows = []
    for cluster_id, group in df.groupby("cluster_id"):
        if len(group) > 1:
            dup_rows.append(
                {
                    "cluster_id": cluster_id,
                    "size": len(group),
                    "sources": sorted(group["source"].unique().tolist()),
                    "classes": sorted(group["class_final"].unique().tolist()),
                    "cross_source": group["source"].nunique() > 1,
                }
            )
    duplicates_report = pd.DataFrame(dup_rows)

    return df, duplicates_report
