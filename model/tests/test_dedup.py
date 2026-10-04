from __future__ import annotations

from leafscout_ml.dedup import _hamming, dedup
from leafscout_ml.manifest import build_manifest


def test_hamming_distance_identical_is_zero():
    assert _hamming("abcd1234", "abcd1234") == 0


def test_hamming_distance_differs_by_bit_count():
    # 0x0 vs 0xf differ in all 4 low bits of one hex digit.
    assert _hamming("0", "f") == 4


def test_exact_duplicates_share_a_cluster(toy_crop, toy_raw_dir):
    manifest = build_manifest(toy_raw_dir, toy_crop)
    deduped, report = dedup(manifest)

    h1 = deduped[deduped["path_original"].str.contains("h1.png")].iloc[0]
    dup = deduped[deduped["path_original"].str.contains("dup_of_h1.png")].iloc[0]
    assert h1["cluster_id"] == dup["cluster_id"]


def test_near_duplicate_phash_is_clustered(toy_crop, toy_raw_dir):
    manifest = build_manifest(toy_raw_dir, toy_crop)
    deduped, report = dedup(manifest, phash_threshold=10)  # generous threshold for tiny toy images

    r1 = deduped[deduped["path_original"].str.contains("/r1.png")].iloc[0]
    near_r1 = deduped[deduped["path_original"].str.contains("near_r1.png")].iloc[0]
    assert r1["cluster_id"] == near_r1["cluster_id"]


def test_distinct_images_are_not_merged(toy_crop, toy_raw_dir):
    manifest = build_manifest(toy_raw_dir, toy_crop)
    deduped, _ = dedup(manifest, phash_threshold=1)  # strict threshold

    healthy_cluster_ids = set(
        deduped[deduped["class_final"] == "healthy"]["cluster_id"]
    )
    rust_cluster_ids = set(deduped[deduped["class_final"] == "rust"]["cluster_id"])
    assert healthy_cluster_ids.isdisjoint(rust_cluster_ids)


def test_duplicates_report_flags_cross_source_clusters(toy_crop, toy_raw_dir):
    manifest = build_manifest(toy_raw_dir, toy_crop)
    _, report = dedup(manifest)

    assert len(report) >= 1
    assert report["cross_source"].any()


def test_every_row_keeps_a_cluster_id_even_if_unique(toy_crop, toy_raw_dir):
    manifest = build_manifest(toy_raw_dir, toy_crop)
    deduped, _ = dedup(manifest, phash_threshold=1)
    assert deduped["cluster_id"].notna().all()
    assert len(deduped) == len(manifest)
