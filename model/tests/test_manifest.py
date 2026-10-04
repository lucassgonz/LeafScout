from __future__ import annotations

import pytest

from leafscout_ml.manifest import build_manifest, classify_folder, file_md5


def test_classify_folder_matches_substring(toy_crop):
    assert classify_folder("sourcea", "healthy", toy_crop.class_map) == "healthy"
    assert classify_folder("sourceb", "rusty", toy_crop.class_map) == "rust"


def test_classify_folder_none_for_excluded_class(toy_crop):
    assert classify_folder("sourceb", "other_species", toy_crop.class_map) is None


def test_classify_folder_unknown_raises(toy_crop):
    with pytest.raises(KeyError):
        classify_folder("sourcea", "totally_unexpected", toy_crop.class_map)


def test_classify_folder_unknown_source_raises(toy_crop):
    with pytest.raises(KeyError):
        classify_folder("sourcez", "healthy", toy_crop.class_map)


def test_build_manifest_scans_all_sources_and_skips_unrecognized(toy_crop, toy_raw_dir):
    df = build_manifest(toy_raw_dir, toy_crop)

    # 4 images in sourcea (healthy x2, rust x2) + 4 in sourceb (healthy x2, rust x2)
    # 'other_species' (excluded) and 'unexpected_folder' (unrecognized) must NOT appear.
    assert len(df) == 8
    assert set(df["source"]) == {"sourcea", "sourceb"}
    assert set(df["class_final"]) == {"healthy", "rust"}


def test_build_manifest_computes_md5(toy_crop, toy_raw_dir):
    df = build_manifest(toy_raw_dir, toy_crop)
    assert df["md5"].notna().all()
    assert df["md5"].str.len().eq(32).all()


def test_build_manifest_exact_duplicate_has_matching_md5(toy_crop, toy_raw_dir):
    df = build_manifest(toy_raw_dir, toy_crop)
    h1 = df[df["path_original"].str.contains("h1.png")]
    dup = df[df["path_original"].str.contains("dup_of_h1.png")]
    assert h1.iloc[0]["md5"] == dup.iloc[0]["md5"]


def test_build_manifest_respects_sources_filter(toy_crop, toy_raw_dir):
    df = build_manifest(toy_raw_dir, toy_crop, sources=["sourcea"])
    assert set(df["source"]) == {"sourcea"}
    assert len(df) == 4


def test_build_manifest_missing_source_dir_is_skipped_not_crashed(toy_crop, tmp_path):
    empty_raw = tmp_path / "empty_raw"
    empty_raw.mkdir()
    df = build_manifest(empty_raw, toy_crop)
    assert len(df) == 0
    assert list(df.columns) == ["path_original", "source", "class_original", "class_final", "md5", "phash"]


def test_file_md5_is_stable(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"hello world")
    assert file_md5(p) == file_md5(p)
    q = tmp_path / "b.bin"
    q.write_bytes(b"hello world!")
    assert file_md5(p) != file_md5(q)
